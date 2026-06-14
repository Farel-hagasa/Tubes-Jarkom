import socket
import time
import argparse
import statistics

# ==========================
# KONFIGURASI
# ==========================

PROXY_IP = "192.168.100.5"   # GANTI DENGAN IP PROXY
PROXY_PORT = 8080

SERVER_IP = "192.168.100.13"  # GANTI DENGAN IP SERVER
UDP_PORT = 9000

# ==========================
# MODE TCP
# ==========================

def tcp_mode():

    request = (
        "GET /index.html HTTP/1.1\r\n"
        f"Host: {PROXY_IP}\r\n"
        "Connection: close\r\n\r\n"
    )

    try:

        client = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        client.connect(
            (
                PROXY_IP,
                PROXY_PORT
            )
        )

        start = time.time()

        client.sendall(
            request.encode()
        )

        response = b""

        while True:

            data = client.recv(4096)

            if not data:
                break

            response += data

        end = time.time()

        response_time = (
            end - start
        ) * 1000

        print("\n===== HTTP RESPONSE =====\n")

        print(
            response.decode(
                errors="ignore"
            )
        )

        print(
            f"\nResponse Time: "
            f"{response_time:.2f} ms"
        )

    except Exception as e:

        print(
            "TCP Error:",
            e
        )

    finally:

        client.close()

# ==========================
# MODE UDP QoS
# ==========================

def udp_mode():

    udp = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    udp.settimeout(1)

    sent_packets = 10
    received_packets = 0

    rtts = []

    total_bytes = 0

    print(
        "\n===== UDP QoS TEST =====\n"
    )

    test_start = time.time()

    for seq in range(
        1,
        sent_packets + 1
    ):

        send_time = time.time()

        payload = (
            f"Ping {seq} "
            f"{send_time}"
        )

        try:

            udp.sendto(
                payload.encode(),
                (
                    SERVER_IP,
                    UDP_PORT
                )
            )

            data, addr = (
                udp.recvfrom(
                    4096
                )
            )

            recv_time = time.time()

            rtt = (
                recv_time
                - send_time
            ) * 1000

            rtts.append(
                rtt
            )

            received_packets += 1

            total_bytes += len(
                data
            )

            print(
                f"Ping {seq}: "
                f"RTT={rtt:.2f} ms"
            )

        except socket.timeout:

            print(
                f"Ping {seq}: "
                f"Request Timed Out"
            )

        time.sleep(1)

    test_end = time.time()

    duration = (
        test_end
        - test_start
    )

    print(
        "\n===== QoS RESULT ====="
    )

    if len(rtts) > 0:

        min_rtt = min(
            rtts
        )

        avg_rtt = (
            sum(rtts)
            / len(rtts)
        )

        max_rtt = max(
            rtts
        )

        print(
            f"Min RTT : "
            f"{min_rtt:.2f} ms"
        )

        print(
            f"Avg RTT : "
            f"{avg_rtt:.2f} ms"
        )

        print(
            f"Max RTT : "
            f"{max_rtt:.2f} ms"
        )

        if len(rtts) > 1:

            differences = []

            for i in range(
                1,
                len(rtts)
            ):

                differences.append(
                    abs(
                        rtts[i]
                        - rtts[i - 1]
                    )
                )

            if len(differences) > 1:

                jitter = (
                    statistics.stdev(
                        differences
                    )
                )

            else:

                jitter = 0

        else:

            jitter = 0

        print(
            f"Jitter : "
            f"{jitter:.2f} ms"
        )

    else:

        print(
            "Tidak ada paket yang diterima"
        )

        jitter = 0

    packet_loss = (
        (
            sent_packets
            - received_packets
        )
        / sent_packets
    ) * 100

    print(
        f"Packet Loss : "
        f"{packet_loss:.2f}%"
    )

    throughput = (
        total_bytes * 8
    ) / duration

    print(
        f"Throughput : "
        f"{throughput:.2f} bps"
    )

    udp.close()

# ==========================
# MAIN
# ==========================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        required=True,
        choices=[
            "tcp",
            "udp"
        ]
    )

    args = parser.parse_args()

    if args.mode == "tcp":

        tcp_mode()

    elif args.mode == "udp":

        udp_mode()


if __name__ == "__main__":

    main()