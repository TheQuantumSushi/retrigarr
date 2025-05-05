# Import required modules
from datetime import datetime, timezone
import transmission_rpc
from transmission_rpc.client import Client

OUTPUT_FILE = "/output/test_script_output.txt"

# Toggle to exclude detecting finished via is_finished or percent_done heuristic
def fetch_and_save_torrents(
    host: str = "transmission-vpn",
    port: int = 9091,
    user: str | None = None,
    password: str | None = None,
    use_percent_done_for_finished: bool = True
) -> None:
    """
    Connect to Transmission RPC and write selected torrent info with elapsed times to OUTPUT_FILE.
    """
    tc = Client(host=host, port=port, username=user, password=password)
    torrents = tc.get_torrents()
    lines: list[str] = []

    now = datetime.now(timezone.utc)
    for idx, torrent in enumerate(torrents, start=1):
        # Name
        name = torrent.name or "N/A"

        # Age since added
        if isinstance(torrent.added_date, datetime):
            age_sec = int((now - torrent.added_date).total_seconds())
            hrs, rem = divmod(age_sec, 3600)
            mins, secs = divmod(rem, 60)
            age_hms = f"{hrs}h{mins}m{secs}s"
        else:
            age_sec = "N/A"
            age_hms = "N/A"

        # Time since last activity
        if isinstance(torrent.activity_date, datetime):
            elapsed_sec = int((now - torrent.activity_date).total_seconds())
            hrs2, rem2 = divmod(elapsed_sec, 3600)
            mins2, secs2 = divmod(rem2, 60)
            elapsed_hms = f"{hrs2}h{mins2}m{secs2}s"
        else:
            elapsed_sec = "N/A"
            elapsed_hms = "N/A"

        # Finished? Use percent_done >= 1.0 or API flag based on toggle
        if use_percent_done_for_finished:
            finished = isinstance(torrent.percent_done, (int, float)) and torrent.percent_done >= 1.0
        else:
            finished = bool(getattr(torrent, 'is_finished', False))

        # Status code/name
        status = torrent.status or "N/A"

        # Build output
        lines.append(f"{idx}. {name}")
        lines.append(f"   - Age in seconds               : {age_sec}")
        lines.append(f"   - Age (h/m/s)                  : {age_hms}")
        lines.append(f"   - Time since last activity (s) : {elapsed_sec}")
        lines.append(f"   - Time since last activity     : {elapsed_hms}")
        lines.append(f"   - Finished                     : {finished}")

        if finished:
            # Seeding? speed > 0
            rate_up = torrent.rate_upload or 0
            seeding = rate_up > 0
            lines.append(f"   - Seeding                      : {seeding}")
            if seeding:
                lines.append(f"   - Seeding speed                : {rate_up} B/s")
        else:
            # Progress percentage
            if isinstance(torrent.percent_done, (int, float)):
                pct = torrent.percent_done * 100
                progress_str = f"{pct:.1f}%"
            else:
                progress_str = "N/A"
            lines.append(f"   - Progress                     : {progress_str}")

            # ETA until done
            eta = torrent.eta
            if isinstance(eta, (int, float)) and eta > 0:
                hrs3, rem3 = divmod(int(eta), 3600)
                mins3, secs3 = divmod(rem3, 60)
                eta_hms = f"{hrs3}h{mins3}m{secs3}s"
                lines.append(f"   - ETA until done               : {eta_hms}")
            else:
                lines.append(f"   - ETA until done               : N/A")

            # Download speed
            dl_rate = torrent.rate_download if torrent.rate_download is not None else "N/A"
            lines.append(f"   - Download speed               : {dl_rate} B/s")

            # Stalled?
            stalled = bool(torrent.is_stalled)
            lines.append(f"   - Stalled                      : {stalled}")

        # Status
        lines.append(f"   - Status                       : {status}")
        lines.append("")  # blank line

    # Write to output file
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    # Pass False to use the Transmission API flag, True to use percent_done heuristic
    fetch_and_save_torrents(use_percent_done_for_finished=True)
