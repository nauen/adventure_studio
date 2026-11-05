import unittest

from adventure_studio.image_pipeline import FixtureImageProvider, ImageRequest, IndexedImage


class ImagePipelineTests(unittest.TestCase):
    def test_offline_provider_is_repeatable(self):
        image = IndexedImage(b"\x00\x01\x01\x00", ((0, 0, 0), (255, 2, 3)), 2, 2, "fixture:v1")
        provider = FixtureImageProvider({"kitchen": image})
        request = ImageRequest("kitchen", "An old kitchen", 2, 2)
        self.assertEqual(provider.generate(request).digest, provider.generate(request).digest)
        self.assertEqual(len(image.digest), 64)

    def test_unknown_asset_and_size_mismatch_are_explicit(self):
        image = IndexedImage(b"\x00", ((0, 0, 0),), 1, 1, "fixture:v1")
        provider = FixtureImageProvider({"kitchen": image})
        with self.assertRaisesRegex(ValueError, "Missing generated asset"):
            provider.generate(ImageRequest("door", "Door", 1, 1))
        with self.assertRaisesRegex(ValueError, "dimensions disagree"):
            provider.generate(ImageRequest("kitchen", "Kitchen", 2, 1))

    def test_invalid_indexed_assets_rejected(self):
        for pixels, palette in ((b"\x00\x01", ((0, 0, 0),)),
                                (b"\x00", ((256, 0, 0),)), (b"\x00", ())):
            with self.subTest(pixels=pixels, palette=palette), self.assertRaises(ValueError):
                IndexedImage(pixels, palette, 1, 1, "fixture:v1")

    def test_invalid_request_rejected(self):
        with self.assertRaises(ValueError):
            ImageRequest("../secret", "scene", 320, 200)
        with self.assertRaises(ValueError):
            ImageRequest("scene", " ", 320, 200)


if __name__ == "__main__":
    unittest.main()
