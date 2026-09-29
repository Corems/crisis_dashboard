import grpc

from app.grpc.servicer import CrisisServicer

try:
    from app.grpc import crisis_pb2_grpc
except ImportError:
    crisis_pb2_grpc = None


async def serve_grpc(port: int = 50051):
    if crisis_pb2_grpc is None:
        print("gRPC proto not generated yet, skipping gRPC server")
        return

    server = grpc.aio.server()
    crisis_pb2_grpc.add_CrisisServiceServicer_to_server(CrisisServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    await server.start()
    print(f"gRPC server listening on :{port}")
    await server.wait_for_termination()
