# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
import mirror_pb2 as mirror__pb2


class AudioServiceStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.sendAudio = channel.unary_unary(
        '/AudioService/sendAudio',
        request_serializer=mirror__pb2.AudioChunk.SerializeToString,
        response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )


class AudioServiceServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def sendAudio(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_AudioServiceServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'sendAudio': grpc.unary_unary_rpc_method_handler(
          servicer.sendAudio,
          request_deserializer=mirror__pb2.AudioChunk.FromString,
          response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'AudioService', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))