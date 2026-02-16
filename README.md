# Python Audio Streamer

Stream audio from one machine to another over your local network using UDP.

## Requirements

- Python 3.7+
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)

### Install PyAudio

**Windows:**
```bash
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install python3-pyaudio portaudio19-dev
# or via pip after installing portaudio:
pip install pyaudio
```

## Usage

### 1. Start the receiver (on your PC)

```bash
python receiver.py
```

This listens on UDP port 4000 by default.

### 2. Start the sender (on your laptop)

```bash
python sender.py <RECEIVER_IP>
```

Replace `<RECEIVER_IP>` with the local IP of the machine running the receiver (e.g. `192.168.1.100`).

### Finding your local IP

- **Windows:** `ipconfig` — look for the IPv4 address under your Wi-Fi or Ethernet adapter.
- **macOS/Linux:** `ip addr` or `ifconfig` — look for the address on `wlan0`, `en0`, or similar.

## Options

Both scripts share common options:

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | `4000` | UDP port to use |
| `--channels` | `1` | Number of audio channels (1 = mono, 2 = stereo) |
| `--rate` | `44100` | Sample rate in Hz |
| `--device` | system default | Audio device index |
| `--list` | — | List available audio devices and exit |

### Examples

List audio devices:
```bash
python sender.py 0.0.0.0 --list
python receiver.py --list
```

Stream in stereo on a custom port:
```bash
# Receiver
python receiver.py --port 5000 --channels 2

# Sender
python sender.py 192.168.1.100 --port 5000 --channels 2
```

Use a specific audio device:
```bash
python sender.py 192.168.1.100 --device 2
```

## How it works

- **sender.py** captures audio from an input device using PyAudio, then sends raw PCM chunks over UDP to the receiver's IP.
- **receiver.py** binds to a UDP port, receives audio chunks, and writes them to an output device via PyAudio.

UDP is used for low-latency delivery. Packets that arrive late or out of order are simply played as-is, which is acceptable for real-time audio where low latency matters more than perfect reliability.

## Firewall

Make sure the UDP port (default `4000`) is open on the receiver machine. On Windows, you may need to allow it through Windows Firewall. On Linux:

```bash
sudo ufw allow 4000/udp
```

## Troubleshooting

- **No sound:** Check that the receiver's firewall allows incoming UDP on the chosen port. Verify both machines are on the same network.
- **Choppy audio:** Try reducing `--rate` to `22050` or switching to a wired connection.
- **Device errors:** Use `--list` to see available devices and pick the correct `--device` index.
- **Permission denied (Linux):** You may need to add your user to the `audio` group: `sudo usermod -aG audio $USER`.
