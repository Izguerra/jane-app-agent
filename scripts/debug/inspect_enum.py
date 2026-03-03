from livekit import rtc
print("Members of ConnectionState:")
print("TrackKind keys:", rtc.TrackKind.keys())
print("Track.Kind values:", [(k, int(v)) for k, v in rtc.TrackKind.items()])
