#include <iostream>
#include <string>
#include <queue>
#include <mutex>

#include <grpc++/grpc++.h>
#include "mirror.grpc.pb.h"

class AudioServiceImpl final : public AudioService::Service
{
    public:
        grpc::Status SendAudio(
            grpc::ServerContext *context,
            const AudioChunk *audioChunk,
            Empty *empty) override
        {
            // push messages into the input queue as fast as possible
            mInputLock.lock();
            mIncomingMessages.push(*audioChunk);

            // if it's been longer than 1 * sampling_rate (44.1khz) then sum all the samples we took and add it to the output queue
            if (std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now() - mLastTime).count() > mLoopTimeNs)
            {
                std::int16_t summed[1024] = {0};

                while (!mIncomingMessages.empty())
                {
                    auto currentMessage = mIncomingMessages.front();
                    mIncomingMessages.pop();

                    std::int16_t * messageInt = (std::int16_t *) &currentMessage.data()[0u];

                    for (int i = 0; i < 1024; i++)
                        summed[i] += messageInt[i];
                }

                AudioChunk outgoing;
                outgoing.set_id(audioChunk->id());
                outgoing.set_sender(audioChunk->sender());
                outgoing.set_data(std::string((const char *) summed, 2048));

                mOutputLock.lock();
                mOutgoingMessages.push(outgoing);
                mOutputLock.unlock();

                mLastTime = std::chrono::high_resolution_clock::now();
            }
            mInputLock.unlock();
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
        std::queue<AudioChunk> mIncomingMessages;
        std::queue<AudioChunk> mOutgoingMessages;
        const int mLoopTimeNs = 45351;
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
