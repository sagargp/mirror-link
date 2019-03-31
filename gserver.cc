#include <iostream>
#include <string>
#include <queue>
#include <mutex>
#include <algorithm>

#include <grpc++/grpc++.h>
#include "mirror.grpc.pb.h"



#define FRAMESPERBUFFER 2048
#define LOOPTIMENS 22675


class AudioServiceImpl final : public AudioService::Service
{
    public:
        grpc::Status SendAudioStream(grpc::ServerContext *context, grpc::ServerReader<AudioChunk> *reader, Empty *empty) override
        {
            AudioChunk chunk;

            while (reader->Read(&chunk))
            {
                std::lock_guard<std::mutex> _(mInputLock);
                mIncomingMessages.push_back(chunk);

                if (std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now() - mLastTime).count() > LOOPTIMENS)
                {
                    float summed_float[FRAMESPERBUFFER] = {0.0f};

                    for (auto currentMessage : mIncomingMessages)
                    {
                        std::int16_t * messageInt = (std::int16_t *) &currentMessage.data()[0u];
                        for (int i = 0; i < FRAMESPERBUFFER; i++)
                            summed_float[i] += float(messageInt[i]);
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
            return grpc::Status::OK;
        }

        grpc::Status SendAudio(grpc::ServerContext *context, const AudioChunk *audioChunk, Empty *empty) override
        {
            // audioChunk->data() contains 2048 int16's that represent 2048 samples of audio
            // push these into an input queue as fast as we can
            std::lock_guard<std::mutex> _in(mInputLock);

            mIncomingMessages.push_back(*audioChunk);

            // if a sampling cycle has passed, take all the messages (2048 samples each) and sum them together
            if (std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now() - mLastTime).count() > LOOPTIMENS)
            {
                float summed_float[FRAMESPERBUFFER] = {0.0f};

                for (auto currentMessage : mIncomingMessages)
                {
                    std::int16_t * messageInt = (std::int16_t *) &currentMessage.data()[0u];
                    for (int i = 0; i < FRAMESPERBUFFER; i++)
                        summed_float[i] += float(messageInt[i]);
                }
                mIncomingMessages.clear();

                std::int16_t summed[FRAMESPERBUFFER];

                for (int i = 0; i < FRAMESPERBUFFER; i++)
                    summed[i] = std::min(std::int16_t(summed_float[i]), std::numeric_limits<std::int16_t>::max());

                AudioChunk outgoing;
                outgoing.set_id(audioChunk->id());
                outgoing.set_sender(audioChunk->sender());

                // Send out the data as a string -- that is, 2048 int16's become 4096 chars
                outgoing.set_data(std::string((const char *) summed, 2*FRAMESPERBUFFER));

                std::lock_guard<std::mutex> _out(mOutputLock);
                mOutgoingMessages.push(outgoing);
                mOutputLock.unlock();

                mLastTime = std::chrono::high_resolution_clock::now();
            }
            return grpc::Status::OK;
        }

        grpc::Status GetAudioStream(grpc::ServerContext *context,
            const Empty *empty,
            grpc::ServerWriter<AudioChunk> *audioChunkStream) override
        {
            while (!mOutgoingMessages.empty())
            {
                mOutputLock.lock();
                audioChunkStream->Write(mOutgoingMessages.front());
                mOutgoingMessages.pop();
                mOutputLock.unlock();
            }
            return grpc::Status::OK;
        }

    private:
        std::mutex mInputLock;
        std::mutex mOutputLock;
        std::chrono::time_point<std::chrono::high_resolution_clock> mLastTime;
        std::vector<AudioChunk> mIncomingMessages;
        std::queue<AudioChunk> mOutgoingMessages;
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
