#include <iostream>
#include <string>
#include <queue>
#include <mutex>
#include <algorithm>

#include <grpc++/grpc++.h>
#include "mirror.grpc.pb.h"


#define FRAMESPERBUFFER 2048
#define LOOPTIMEMS 46


class AudioServiceImpl final : public AudioService::Service
{
    public:
        void enqueueChunk(const AudioChunk &chunk)
        {
            std::lock_guard<std::mutex> _(mInputLock);
            mIncomingMessages.insert(std::pair<std::string, AudioChunk>(chunk.sender(), chunk));

            if (std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now() - mLastTime).count() > LOOPTIMEMS)
            {
                std::cout << "summing together " << mIncomingMessages.size() << " chunks" << std::endl;
                float summed_float[FRAMESPERBUFFER] = {0.0f};

                for (std::pair<std::string, AudioChunk> currentMessage : mIncomingMessages)
                {
                    std::int16_t * messageInt = (std::int16_t *) &currentMessage.second.data()[0u];
                    for (int i = 0; i < FRAMESPERBUFFER; i++)
                    {
                        float a = summed_float[i];
                        float b= (float) messageInt[i];
                        summed_float[i] = a + b - a * b;
                    }
                }
                mIncomingMessages.clear();

                std::int16_t summed[FRAMESPERBUFFER];

                for (int i = 0; i < FRAMESPERBUFFER; i++)
                    summed[i] = std::min(std::int16_t(summed_float[i]), std::numeric_limits<std::int16_t>::max());

                AudioChunk outgoing;
                outgoing.set_id(chunk.id());
                outgoing.set_sender(chunk.sender());

                // Send out the data as a string -- that is, 2048 int16's become 4096 chars
                outgoing.set_data(std::string((const char *) summed, 2*FRAMESPERBUFFER));

                {
                    std::lock_guard<std::mutex> _out(mOutputLock);
                    mOutgoingMessages.push(outgoing);
                }
                mLastTime = std::chrono::high_resolution_clock::now();
            }
        }

        grpc::Status SendAudioStream(grpc::ServerContext *context, grpc::ServerReader<AudioChunk> *reader, Empty *empty) override
        {
            AudioChunk chunk;
            while (reader->Read(&chunk))
                enqueueChunk(chunk);
            return grpc::Status::OK;
        }

        grpc::Status SendAudio(grpc::ServerContext *context, const AudioChunk *chunk, Empty *empty) override
        {
            enqueueChunk(*chunk);
            return grpc::Status::OK;
        }

        grpc::Status GetAudioStream(grpc::ServerContext *context, const Empty *empty, grpc::ServerWriter<AudioChunk> *audioChunkStream) override
        {
            while (!mOutgoingMessages.empty())
            {
                std::lock_guard<std::mutex> _(mOutputLock);
                audioChunkStream->Write(mOutgoingMessages.front());
                mOutgoingMessages.pop();
            }
            return grpc::Status::OK;
        }

    private:
        std::mutex mInputLock;
        std::mutex mOutputLock;
        std::map<std::string, AudioChunk> mIncomingMessages;
        std::queue<AudioChunk> mOutgoingMessages;
        std::chrono::time_point<std::chrono::high_resolution_clock> mLastTime;
};

void RunServer() {
  std::string server_address("0.0.0.0:9999");
  AudioServiceImpl service;

  grpc::ServerBuilder builder;
  // Listen on the given address without any authentication mechanism.
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  // Register "service" as the instance through which we'll communicate with
  // clients. In this case it corresponds to an *synchronous* service.
  builder.RegisterService(&service);
  // Finally assemble the server.
  std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
  std::cout << "Server listening on " << server_address << std::endl;

  // Wait for the server to shutdown. Note that some other thread must be
  // responsible for shutting down the server for this call to ever return.
  server->Wait();
}

int main(int argc, char** argv) {
  RunServer();

  return 0;
}
