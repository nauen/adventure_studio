"""Source-level contract for native ScummC Actor declarations and setup."""

import unittest

from adventure_studio.scumm_bootstrap import inject_actor_bindings, inject_actor_room_animations
from adventure_studio.scumm_actor_probe import actor_count_room_source
from adventure_studio.scumm_costume_probe import gesture_fixture
from adventure_studio.scumm_project import ActorAsset
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.scumm_assets import scrolling_fixture, destination_fixture
from dataclasses import replace


class ActorBootstrapTests(unittest.TestCase):
    def test_two_actors_and_shared_costume_are_emitted_without_duplicate_cost(self):
        source = ('room Harbor;\nroom ResRoom {\n'
                  '    cost egoCost = "devil.cost";\n'
                  '    script setupActors() {\n'
                  '        // set VAR_EGO so we can use the *Ego* functions\n'
                  '    }\n}\n')
        header = '// define an actor for our hero\nactor hero;\n'
        actors = (ActorAsset('Companion', 'NativeGesture', 'Harbor', 300, 110, 'W', 'Companion'),
                  ActorAsset('Guide', 'NativeGesture', 'Cellar', 80, 100, 'E'))
        generated, declaration = inject_actor_bindings(source, header, actors,
                                                        (gesture_fixture(),), ('Harbor', 'Cellar'))
        self.assertIn('actor Companion;', declaration)
        self.assertIn('actor Guide;', declaration)
        self.assertEqual(generated.count('cost NativeGestureCost = "NativeGesture.cost";'), 1)
        self.assertIn('putActorAt(Companion, 300, 110, Harbor);', generated)
        self.assertIn('setActorDirection(WEST);', generated)
        self.assertIn('putActorAt(Guide, 80, 100, Cellar);', generated)
        self.assertIn('room Cellar;', generated)
        self.assertIn('setActorName("Companion");', generated)

    def test_empty_actor_set_keeps_legacy_bootstrap_unchanged(self):
        self.assertEqual(inject_actor_bindings('source', 'header', (), (), ('Harbor',)),
                         ('source', 'header'))

    def test_reserved_fixture_hero_is_explicit_export_blocker(self):
        with self.assertRaisesRegex(ValueError, 'reserves the hero'):
            inject_actor_bindings('source', 'header',
                                  (ActorAsset('hero', 'NativeGesture', 'Harbor', 2, 3),),
                                  (gesture_fixture(),), ('Harbor',))

    def test_named_initial_animation_maps_to_native_costume_index(self):
        source = ('room Harbor;\nroom ResRoom {\n'
                  '    cost egoCost = "devil.cost";\n'
                  '    script setupActors() {\n'
                  '        // set VAR_EGO so we can use the *Ego* functions\n'
                  '    }\n}\n')
        header = '// define an actor for our hero\nactor hero;\n'
        actor = ActorAsset('Guide', 'NativeGesture', 'Harbor', 280, 110,
                           initial_animation='gesture')
        document = GameDocument('AnimationTest', (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),), (actor,))
        restored = parse_document(canonical_json(document))
        self.assertEqual(restored, document)
        generated, _ = inject_actor_bindings(source, header, restored.actors,
                                              restored.costumes, ('Harbor', 'Cellar'))
        self.assertNotIn('animateActor(Guide,24);', generated)
        room_source = 'room Harbor {\n        ResRoom::showCursor();\n}\n'
        room_source = inject_actor_room_animations(room_source, 'Harbor',
                                                   restored.actors, restored.costumes)
        self.assertIn('ResRoom::showCursor();\n        animateActor(Guide,24);', room_source)
        self.assertEqual(inject_actor_room_animations(room_source, 'Cellar',
                                                       restored.actors, restored.costumes), room_source)

    def test_initial_animation_rejects_unknown_unindexed_and_missing_direction(self):
        costume = gesture_fixture()
        rooms = (scrolling_fixture(), destination_fixture())
        actor = ActorAsset('Guide', costume.name, rooms[0].name, 20, 100)
        for changed, message in (
            (replace(actor, initial_animation='missing'), 'unknown animation'),
            (replace(actor, initial_animation='stand'), 'explicit native index'),
            (replace(actor, direction='N', initial_animation='gesture'), 'lacks direction'),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                canonical_json(GameDocument('AnimationTest', rooms, (costume,), (changed,)))

    def test_old_actor_json_does_not_gain_animation_field(self):
        actor = ActorAsset('Guide', 'NativeGesture', 'Harbor', 20, 100)
        document = GameDocument('LegacyActor', (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),), (actor,))
        self.assertNotIn('initial_animation', canonical_json(document))

    def test_count_probe_uses_authored_actor_and_negative_control(self):
        source = 'room Harbor {\n        animateActor(Companion,24);\n}\n'
        positive = actor_count_room_source(source, 2)
        control = actor_count_room_source(source, 3)
        self.assertIn('getActorAnimCounter1(Companion) < 2', positive)
        self.assertIn('getActorAnimCounter1(Companion) < 3', control)
        self.assertIn('setObjectState(Key, 0);', positive)
        self.assertLess(positive.index('delaySeconds(2);'),
                        positive.index('animateActor(Companion,24);'))
        self.assertNotIn('getActorAnimCounter1(VAR_EGO)', positive)
        with self.assertRaises(ValueError):
            actor_count_room_source(source, 0)
        with self.assertRaises(ValueError):
            actor_count_room_source('room Harbor {}', 2)


if __name__ == '__main__':
    unittest.main()
