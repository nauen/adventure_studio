import pytest

from adventure_studio.image_pipeline import FixtureImageProvider, ImageRequest, IndexedImage


def test_offline_provider_is_repeatable():
    image = IndexedImage(b"\x00\x01\x01\x00", ((0, 0, 0), (255, 2, 3)), 2, 2, "fixture:v1")
    provider = FixtureImageProvider({"kitchen": image})
    request = ImageRequest("kitchen", "An old kitchen", 2, 2)
    assert provider.generate(request).digest == provider.generate(request).digest
    assert len(image.digest) == 64


def test_unknown_asset_and_size_mismatch_are_explicit():
    image = IndexedImage(b"\x00", ((0, 0, 0),), 1, 1, "fixture:v1")
    provider = FixtureImageProvider({"kitchen": image})
    with pytest.raises(ValueError, match="Missing generated asset"):
        provider.generate(ImageRequest("door", "Door", 1, 1))
    with pytest.raises(ValueError, match="dimensions disagree"):
        provider.generate(ImageRequest("kitchen", "Kitchen", 2, 1))


@pytest.mark.parametrize("pixels,palette", [
    (b"\x00\x01", ((0, 0, 0),)),
    (b"\x00", ((256, 0, 0),)),
    (b"\x00", ()),
])
def test_invalid_indexed_assets_rejected(pixels, palette):
    with pytest.raises(ValueError):
        IndexedImage(pixels, palette, 1, 1, "fixture:v1")


def test_invalid_request_rejected():
    with pytest.raises(ValueError):
        ImageRequest("../secret", "scene", 320, 200)
    with pytest.raises(ValueError):
        ImageRequest("scene", " ", 320, 200)
