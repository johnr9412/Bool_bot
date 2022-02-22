import spotipy


def get_playlist_tracks(playlist_url, tokens):
    sp = spotipy.Spotify(client_credentials_manager=spotipy.SpotifyClientCredentials(tokens[0], tokens[1]))
    results = sp.playlist_items(playlist_url)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks


def get_albums_from_tracks(tracks):
    album_objects = []
    for track in tracks:
        album_objects.append(parse_track_information(track))
    return album_objects


def make_list_distinct(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def parse_track_information(track):
    return track['track']['album']['artists'][0]['name'] + ' - ' + track['track']['album']['name']


def get_albums_from_playlist(playlist_url, tokens):
    tracks = get_playlist_tracks(playlist_url, tokens)
    albums = make_list_distinct(get_albums_from_tracks(tracks))
    return sorted(albums)
