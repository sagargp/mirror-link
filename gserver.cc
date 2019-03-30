#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <string>

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
            mLastMessage.set_id(audioChunk->id());
            mLastMessage.set_sender(audioChunk->sender());
            mLastMessage.set_data(audioChunk->data());

            // implement SendAudio() here
            return grpc::Status::OK;
        }

        grpc::Status GetAudioStream(grpc::ServerContext *context,
            const Empty *empty,
            grpc::ServerWriter<AudioChunk> *audioChunkStream) override
        {
            audioChunkStream->Write(mLastMessage);
            // implement GetAudioStream() here
            return grpc::Status::OK;
        }

    private:
        AudioChunk mLastMessage;

      // The actual database.
      std::map<std::string, std::string> string_db_;
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
