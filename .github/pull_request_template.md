## Ziel / betroffene Fähigkeit

- Capability-ID(s):
- Nutzerfunktion und nativer SCUMM-v6-Pfad:

## Architektur

- [ ] Fachliches Modell, Export-Adapter und SCUMM-Backend bleiben getrennt.
- [ ] Keine unbegründeten 2/3/4/16/64-Limits oder Demo-Annahmen in allgemeinen Modellen.
- [ ] Neue Limits sind als `NATIVE_LIMIT`, `EXPORTER_LIMIT`, `FIXTURE_LIMIT`, `UI_LIMIT` oder `DOMAIN_RULE` klassifiziert und belegt.
- [ ] Keine stille Entfernung von Inhalten oder erfundene Runtime-Operation.
- [ ] Bestehende JSON-Versionen/IDs bleiben kompatibel oder haben eine dokumentierte Migration.

## Tests und Evidenz

- [ ] Bestehende Tests/Fixtures laufen unverändert.
- [ ] Kleine, größere und Grenzfälle sind getestet; bei Mengen 0/1/2/N und Grenze + 1 soweit sinnvoll.
- [ ] SCUMM-Bytecode-/Ressourcenstruktur nachgewiesen.
- [ ] Stock-ScummVM-Gameplay-/Renderingtest nachgewiesen **oder ausdrücklich offen**.

## Projektstand

- [ ] `docs/SCUMM_V6_CAPABILITIES.md` bei Statusänderung aktualisiert.
- [ ] `docs/PROJECT_STATUS.md` mit Ist-Stand, Risiken und nächstem Paket aktualisiert.
- [ ] Architekturentscheidungen bei relevanter Änderung als ADR festgehalten.

Bei reiner Dokumentation nicht anwendbare Felder im PR-Text begründen;
keine unerfüllten Prüfungen als bestanden kennzeichnen.
