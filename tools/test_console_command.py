"""Send one command to the isolated test server's owner-only UNIX socket."""
import argparse
import socket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('socket_path')
    parser.add_argument('command', nargs='+')
    args = parser.parse_args()
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(3)
        connection.connect(args.socket_path)
        connection.sendall((' '.join(args.command) + '\n').encode())
        print(connection.recv(1024).decode(errors='replace').strip())


if __name__ == '__main__':
    main()
