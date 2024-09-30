from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.conf import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
def spotify_login(request):
    sp_oauth = SpotifyOAuth(client_id=settings.SPOTIPY_CLIENT_ID,
                            client_secret=settings.SPOTIPY_CLIENT_SECRET,
                            redirect_uri=settings.SPOTIPY_REDIRECT_URI,
                            scope="user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing")
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)
def clear_session_and_reauthorize(request):
    request.session.flush()
    return redirect('spotify_login')
def spotify_callback(request):
    sp_oauth = SpotifyOAuth(client_id=settings.SPOTIPY_CLIENT_ID,
                            client_secret=settings.SPOTIPY_CLIENT_SECRET,
                            redirect_uri=settings.SPOTIPY_REDIRECT_URI)

    code = request.GET.get('code')
    token_info = sp_oauth.get_access_token(code)
    print(token_info)
    request.session['token_info'] = token_info
    
    return redirect('playlist')
def playlist(request):
    token_info = request.session.get('token_info', None)
    if not token_info:
        return redirect('spotify_login')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    
    return render(request, 'music/playlist.html', {'playlists': playlists['items']})
def index(request):
    return render(request, 'music/index.html')
def playlist(request):
    token_info = get_token(request)
    if not token_info:
        return redirect('spotify_login')

    sp = spotipy.Spotify(auth=token_info['access_token'])

    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        playlist['tracks'] = sp.playlist_tracks(playlist['id'])

    return render(request, 'music/playlist.html', {'playlists': playlists['items']})
def play_track(request, track_id):
    token_info = get_token(request)
    if not token_info:
        return redirect('spotify_login')

    sp = spotipy.Spotify(auth=token_info['access_token'])

    try:
        devices = sp.devices()
        print("Available devices: ", devices)  # Log available devices for debugging
        available_devices = devices.get('devices', [])

        if not available_devices:
            return JsonResponse({"error": "No active Spotify devices found. Please open Spotify on a device and try again."})

        device_id = available_devices[0]['id']
        sp.start_playback(device_id=device_id, uris=[f"spotify:track:{track_id}"])
        return JsonResponse({"status": "playing", "track_id": track_id, "device": device_id})

    except spotipy.exceptions.SpotifyException as e:
        print(f"SpotifyException: {str(e)}")  # Log the exception details
        if e.http_status == 401:
            return clear_session_and_reauthorize(request)
        else:
            return JsonResponse({"error": str(e)})

def get_token(request):
    token_info = request.session.get('token_info', None)
    if not token_info:
        return None

    sp_oauth = SpotifyOAuth(client_id=settings.SPOTIPY_CLIENT_ID,
                            client_secret=settings.SPOTIPY_CLIENT_SECRET,
                            redirect_uri=settings.SPOTIPY_REDIRECT_URI)
    
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        request.session['token_info'] = token_info

    return token_info
