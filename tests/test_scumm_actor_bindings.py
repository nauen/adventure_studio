"""Source-level contract for native ScummC Actor declarations and setup."""

import unittest

from adventure_studio.scumm_bootstrap import inject_actor_bindings
from adventure_studio.scumm_costume_probe import gesture_fixture
from adventure_studio.scumm_project import ActorAsset


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


if __name__ == '__main__':
    unittest.main()
