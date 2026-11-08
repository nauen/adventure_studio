"""Source-level contract for native ScummC Actor declarations and setup."""

import json
import unittest

from adventure_studio.scumm_bootstrap import (inject_actor_bindings, inject_actor_room_animations,
                                              inject_actor_initial_flags,
                                              inject_actor_count_rules)
from adventure_studio.scumm_bootstrap import inject_actor_input_rules
from adventure_studio.scumm_bootstrap import inject_actor_animation_triggers
from adventure_studio.scumm_actor_probe import (actor_count_room_source, actor_binding_room_source,
                                                 project_count_room_source)
from adventure_studio.scumm_costume_probe import gesture_fixture
from adventure_studio.scumm_project import (ActorAsset, ActorCountCondition, ObjectStateEffect,
                                            AnimationRule, AnimationInputRule, AnimationTrigger)
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.scumm_assets import scrolling_fixture, destination_fixture, scummc_room_source
from dataclasses import replace


class ActorBootstrapTests(unittest.TestCase):
    def test_authored_animation_actions_replay_named_costume_without_initial_animation(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 300, 100)
        triggers = (AnimationTrigger('Companion', 'Harbor', 'Key', 'Push', 'gesture'),
                    AnimationTrigger('Companion', 'Harbor', 'Key', 'Pull', 'gesture'))
        document = GameDocument('ReplayAnimation', (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),), (actor,), animation_triggers=triggers)
        self.assertEqual(parse_document(canonical_json(document)), document)
        source = ('room Harbor {\n    object Key {\n'
                  '        verb(int vrb, int objA, int objB) {\n'
                  '        }\n    }\n    local script entry() {\n    }\n}\n')
        native = inject_actor_animation_triggers(source, 'Harbor', document.animation_triggers,
                                                 document.actors, document.costumes)
        self.assertIn('case Push:\n            animateActor(Companion,24);\n            return;', native)
        self.assertIn('case Pull:\n            animateActor(Companion,24);\n            return;', native)
        self.assertEqual(native.count('animateActor(Companion,24);'), 2)
        self.assertEqual(inject_actor_animation_triggers(source, 'Cellar', triggers,
                                                         document.actors, document.costumes), source)
        for changed in (replace(triggers[0], actor_id='Missing'),
                        replace(triggers[0], hotspot_id='Missing'),
                        replace(triggers[0], animation='Missing'),
                        replace(triggers[0], verb='LookAt')):
            with self.subTest(trigger=changed), self.assertRaises(ValueError):
                canonical_json(replace(document, animation_triggers=(changed,)))

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
        self.assertEqual(generated.count('setActorAnimSpeed(2);'), 2)

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
        self.assertIn('ResRoom::showCursor();\n        if(!__studioActorInitial0)', room_source)
        self.assertIn('animateActor(Guide,24);', room_source)
        self.assertEqual(inject_actor_room_animations(room_source, 'Cellar',
                                                       restored.actors, restored.costumes), room_source)

    def test_initial_animation_is_not_retriggered_on_room_reentry(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 280, 110,
                           initial_animation='gesture')
        room_source = ('room Harbor {\n    local script entry() {\n'
                       '        ResRoom::showCursor();\n    }\n}\n')
        native = inject_actor_room_animations(room_source, 'Harbor', (actor,),
                                              (gesture_fixture(),))
        self.assertIn('if(!__studioActorInitial0)', native)
        self.assertIn('__studioActorInitial0 = 1;', native)
        self.assertEqual(native.count('animateActor(Companion,24);'), 1)
        declared = inject_actor_initial_flags('actor hero;\n', (actor,))
        self.assertIn('bit __studioActorInitial0;', declared)
        self.assertEqual(inject_actor_initial_flags('unchanged', (replace(actor, initial_animation=None),)),
                         'unchanged')
        with self.assertRaisesRegex(ValueError, 'shared Actor declaration'):
            inject_actor_initial_flags('unexpected', (actor,))
        second = replace(actor, id='Guide')
        both = inject_actor_room_animations(room_source, 'Harbor', (actor, second),
                                            (gesture_fixture(),))
        self.assertIn('if(!__studioActorInitial0)', both)
        self.assertIn('if(!__studioActorInitial1)', both)
        self.assertIn('animateActor(Guide,24);', both)
        declarations = inject_actor_initial_flags('actor hero;\n',
                                                   (actor, second))
        self.assertEqual(declarations.count('bit __studioActorInitial'), 2)

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
        self.assertLess(positive.index('setCameraAt(480);'),
                        positive.index('animateActor(Companion,24);'))
        self.assertIn('putActorAt(Companion, 430, 100, Harbor);', positive)
        self.assertNotIn('getActorAnimCounter1(VAR_EGO)', positive)
        self.assertIn('getActorAnimCounter1(Companion) < 0', actor_count_room_source(source, 0))
        with self.assertRaises(ValueError):
            actor_count_room_source(source, -1)
        with self.assertRaises(ValueError):
            actor_count_room_source('room Harbor {}', 2)

    def test_binding_probe_checks_room_costume_and_native_frame(self):
        source = 'room Harbor {\n        animateActor(Companion,24);\n}\n'
        for kind, expression in (("room", "getActorRoom(Companion) == Harbor"),
                                 ("costume", "getActorCostume(Companion) != 0"),
                                 ("frame", "getActorFrame(Companion) == 24")):
            with self.subTest(kind=kind):
                self.assertIn(expression, actor_binding_room_source(source, kind))
        with self.assertRaises(ValueError):
            actor_binding_room_source(source, "unknown")

    def test_typed_count_rules_round_trip_and_generate_native_watchers(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 300, 100,
                           initial_animation='gesture')
        rules = (AnimationRule(ActorCountCondition('Companion', 1),
                               ObjectStateEffect('Harbor', 'Key', 0)),
                 AnimationRule(ActorCountCondition('Companion', 2),
                               ObjectStateEffect('Harbor', 'Door', 2)))
        document = GameDocument('CountRules', (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),), (actor,), rules)
        serialized = canonical_json(document)
        self.assertEqual(parse_document(serialized), document)
        source = ('room Harbor {\n    local script entry() {\n'
                  '        ResRoom::showCursor();\n    }\n}\n')
        animated = inject_actor_room_animations(source, 'Harbor', document.actors,
                                                document.costumes)
        native = inject_actor_count_rules(animated, 'Harbor', document.animation_rules,
                                          document.actors, document.costumes)
        self.assertIn('while(getActorAnimCounter1(Companion) < 1)', native)
        self.assertIn('while(getActorAnimCounter1(Companion) < 2)', native)
        self.assertIn('setObjectState(Key,0);', native)
        self.assertIn('setObjectState(Door,2);', native)
        self.assertIn('animateActor(Companion,24);\n        watchActorCount0();\n        watchActorCount1();', native)
        self.assertIn('watchActorCount1();\n        }', native)
        self.assertEqual(inject_actor_count_rules(source, 'Cellar', rules,
                                                  document.actors, document.costumes), source)

    def test_typed_count_rules_reject_invalid_references_and_types(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 300, 100,
                           initial_animation='gesture')
        rooms = (scrolling_fixture(), destination_fixture())
        valid = AnimationRule(ActorCountCondition('Companion', 2),
                              ObjectStateEffect('Harbor', 'Key', 0))
        for invalid, expected in (
            (replace(valid, condition=ActorCountCondition('Missing', 2)), 'requires an Actor'),
            (replace(valid, condition=ActorCountCondition('Companion', 0)), 'positive event'),
            (replace(valid, condition=ActorCountCondition('Companion', True)), 'positive event'),
            (replace(valid, condition=ActorCountCondition('Companion', 3)), 'unreachable'),
            (replace(valid, effect=ObjectStateEffect('Cellar', 'Key', 0)), 'effect room'),
            (replace(valid, effect=ObjectStateEffect('Harbor', 'Missing', 0)), 'unknown room hotspot'),
            (replace(valid, effect=ObjectStateEffect('Harbor', 'Key', 3)), 'supported SCUMM object state'),
        ):
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                canonical_json(GameDocument('InvalidRule', rooms, (gesture_fixture(),),
                                             (actor,), (invalid,)))
        without_animation = replace(actor, initial_animation=None)
        with self.assertRaisesRegex(ValueError, 'requires an Actor'):
            canonical_json(GameDocument('InvalidRule', rooms, (gesture_fixture(),),
                                        (without_animation,), (valid,)))
        data = json.loads(canonical_json(GameDocument('CountRules', rooms,
                                                       (gesture_fixture(),), (actor,), (valid,))))
        data['animation_rules'][0]['effect']['script'] = 'arbitrary code'
        with self.assertRaises(ValueError):
            parse_document(json.dumps(data))

    def test_project_count_probe_uses_versioned_rules_not_raw_script_data(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 410, 110,
                           initial_animation='gesture')
        document = GameDocument('CountProbe', (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),), (actor,))
        source = ('room Harbor {\n    local script entry() {\n'
                  '        animateActor(Companion,24);\n    }\n}\n')
        rendered = project_count_room_source(source, document, 2)
        self.assertIn('local script watchActorCount0()', rendered)
        self.assertIn('getActorAnimCounter1(Companion) < 2', rendered)
        self.assertIn('watchActorCount0();', rendered)
        self.assertLess(rendered.index('setCameraAt(480);'),
                        rendered.index('animateActor(Companion,24);'))

    def test_animation_input_rule_roundtrip_and_native_early_late_branches(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 300, 100,
                           initial_animation='gesture')
        rule = AnimationInputRule('Companion', 'Harbor', 'Key', 'Push', 2,
                                  ObjectStateEffect('Harbor', 'Door', 2),
                                  ObjectStateEffect('Harbor', 'Door', 1))
        document = GameDocument('InputWindow', (scrolling_fixture(), destination_fixture()),
                                (gesture_fixture(),), (actor,), (), (rule,))
        serialized = canonical_json(document)
        self.assertEqual(parse_document(serialized), document)
        self.assertIn('"animation_input_rules"', serialized)
        native = inject_actor_input_rules(scummc_room_source(document.rooms[0]),
                                          'Harbor', document.animation_input_rules)
        self.assertIn('case Push:', native)
        self.assertLess(native.index('    object Door;\n'), native.index('    object Key {\n'))
        self.assertIn('if(getActorAnimCounter1(Companion) < 2)', native)
        self.assertIn('setObjectState(Door,2);', native)
        self.assertIn('setObjectState(Door,1);', native)
        self.assertEqual(inject_actor_input_rules(native, 'Cellar', (rule,)), native)
        with self.assertRaisesRegex(ValueError, 'Conflicting native input verb'):
            inject_actor_input_rules(native, 'Harbor', (rule,))

    def test_animation_input_rejects_invalid_rules_and_unknown_fields(self):
        actor = ActorAsset('Companion', 'NativeGesture', 'Harbor', 300, 100,
                           initial_animation='gesture')
        rooms = (scrolling_fixture(), destination_fixture())
        rule = AnimationInputRule('Companion', 'Harbor', 'Key', 'Push', 2,
                                  ObjectStateEffect('Harbor', 'Door', 2),
                                  ObjectStateEffect('Harbor', 'Door', 1))
        for invalid, expected in (
            (replace(rule, actor_id='Unknown'), 'requires an Actor'),
            (replace(rule, room='Cellar'), 'share a room'),
            (replace(rule, hotspot_id='Unknown'), 'unknown hotspot'),
            (replace(rule, verb='LookAt'), 'Unsupported'),
            (replace(rule, before_count=0), 'unreachable'),
            (replace(rule, before_count=True), 'unreachable'),
            (replace(rule, before_count=3), 'unreachable'),
            (replace(rule, on_time=ObjectStateEffect('Cellar', 'Door', 2)), 'target its room'),
            (replace(rule, too_late=ObjectStateEffect('Harbor', 'Missing', 1)), 'unknown hotspot'),
            (replace(rule, too_late=ObjectStateEffect('Harbor', 'Door', 3)), 'object state'),
        ):
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                canonical_json(GameDocument('InputWindow', rooms, (gesture_fixture(),),
                                            (actor,), (), (invalid,)))
        with self.assertRaisesRegex(ValueError, 'Duplicate animation input'):
            canonical_json(GameDocument('InputWindow', rooms, (gesture_fixture(),),
                                        (actor,), (), (rule, rule)))
        document = GameDocument('InputWindow', rooms, (gesture_fixture(),),
                                (actor,), (), (rule,))
        data = json.loads(canonical_json(document))
        data['animation_input_rules'][0]['on_time']['script'] = 'arbitrary script'
        with self.assertRaisesRegex(ValueError, 'Invalid document fields'):
            parse_document(json.dumps(data))


if __name__ == '__main__':
    unittest.main()
