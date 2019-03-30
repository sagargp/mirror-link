CXX = g++
CPPFLAGS += -I/usr/local/include -pthread
CXXFLAGS += -std=c++11
LDFLAGS += -L/usr/local/lib -lgrpc++_unsecure -lgrpc -lprotobuf -lpthread -ldl
PROTOC = protoc
GRPC_CPP_PLUGIN = grpc_cpp_plugin
GRPC_CPP_PLUGIN_PATH ?= `which $(GRPC_CPP_PLUGIN)`
GRPC_PYTHON_PLUGIN = grpc_python_plugin
GRPC_PYTHON_PLUGIN_PATH ?= `which $(GRPC_PYTHON_PLUGIN)`

EXECUTABLES = gserver

all: $(EXECUTABLES) py

.PRECIOUS: %.grpc.pb.cc
%.grpc.pb.cc: %.proto
	$(PROTOC) --grpc_out=. --plugin=protoc-gen-grpc=$(GRPC_CPP_PLUGIN_PATH) $<

.PRECIOUS: %.pb.cc
%.pb.cc: %.proto
	$(PROTOC) --cpp_out=. $<

gserver: mirror.pb.o mirror.grpc.pb.o gserver.o
	$(CXX) $^ $(LDFLAGS) -o $@

# Rule for producing the Python protobuf bindings
py: mirror.proto
	env/bin/python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. $<

clean:
	rm -f $(EXECUTABLES) *.pb.cc *.pb.h *.pb.o *.o *_pb2.py *.pyc *_pb2_grpc.py


