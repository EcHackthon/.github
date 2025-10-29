from dataclasses import dataclass

from src.spotify.client import SpotifyClient
from src.spotify.recommendation import RecommendationRequest


@dataclass
class DummyTokenManager:
    calls: int = 0

    def get_access_token(self) -> str:
        self.calls += 1
        return "token"

    def invalidate(self) -> None:
        pass


class DummySession:
    def __init__(self, response):
        self._response = response
        self.request_args = None

    def request(self, method, url, **kwargs):
        self.request_args = (method, url, kwargs)
        return self._response


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if 400 <= self.status_code:
            raise AssertionError("HTTP error triggered in test")


def test_builds_spotify_parameters():
    token_manager = DummyTokenManager()
    response = DummyResponse({"tracks": []})
    client = SpotifyClient(token_manager=token_manager, user_id="user", session=DummySession(response))

    request = RecommendationRequest(mood="positive", rationale="test", limit=3)
    results = client.recommend_for_mood(request)

    assert len(results) == 1
    method, url, kwargs = client._session.request_args  # type: ignore[attr-defined]
    assert method == "GET"
    assert "seed_genres" in kwargs["params"]
    assert kwargs["params"]["limit"] == "3"
    assert token_manager.calls == 1


def test_retries_when_unauthorised():
    token_manager = DummyTokenManager()
    failing_response = DummyResponse({"tracks": []}, status_code=401)
    success_response = DummyResponse({"tracks": []})
    session = DummySession(failing_response)

    def request(method, url, **kwargs):
        if not getattr(session, "retried", False):
            session.retried = True
            return failing_response
        return success_response

    session.request = request  # type: ignore[assignment]
    client = SpotifyClient(token_manager=token_manager, user_id="user", session=session)

    request_obj = RecommendationRequest(mood="neutral", rationale="test")
    client.recommend_for_mood(request_obj)

    assert token_manager.calls == 2


def test_playlist_fallback_when_recommendations_empty():
    token_manager = DummyTokenManager()
    session = DummySession(None)

    def request(method, url, **kwargs):
        if url.endswith("/v1/recommendations"):
            return DummyResponse({"tracks": []})
        if "/v1/playlists/playlist123/tracks" in url:
            return DummyResponse(
                {
                    "items": [
                        {
                            "track": {
                                "id": "abc",
                                "name": "Fallback Song",
                                "artists": [{"name": "Artist"}],
                                "preview_url": None,
                                "external_urls": {"spotify": "https://example.com"},
                            }
                        }
                    ]
                }
            )
        raise AssertionError("Unexpected URL: " + url)

    session.request = request  # type: ignore[assignment]
    client = SpotifyClient(
        token_manager=token_manager,
        user_id="user",
        session=session,
        recommended_playlist_id="playlist123",
    )

    request_obj = RecommendationRequest(mood="calm", rationale="test", limit=1)
    results = client.recommend_for_mood(request_obj)

    assert len(results[0].tracks) == 1
    assert results[0].tracks[0].id == "abc"
    assert token_manager.calls == 2
