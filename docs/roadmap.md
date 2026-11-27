# Adventure Studio – aktive Produktroadmap

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; Studio/JSON-v1/Story → ScummC-v6 → unverändertes stock ScummVM. NPC-Komfort nach #190 beendet.
- **Konsolidierung (27.11.2026):** Produktbasis [316372ef](https://github.com/nauen/adventure_studio/commit/316372ef31035691c266b50dd5450f4685eb7d63), [Main-Core 45977321845](https://github.com/nauen/adventure_studio/actions/runs/45977321845) grün. #325 integriert: native Positionierung transferierter Actors inklusive Anwesenheitsguard und Escape-Endposition; [Core 45960515920](https://github.com/nauen/adventure_studio/actions/runs/45960515920), [Native/Studio 45960522776](https://github.com/nauen/adventure_studio/actions/runs/45960522776) grün; Geometry-Positionsprüfung und [Artefakt 15180507693](https://github.com/nauen/adventure_studio/actions/runs/45960522776/artifacts/15180507693) erfolgreich. R01 #335 (256 Farben, vollständiger UI-Import offen), R06 #323/#325, R07 #258 (IM02/ZP04), R08 #264 (konkaver Korridor) und R09 #267 (zwei reversible Gates über Raumrückkehr) sind integrierte Teilfähigkeiten, kein vollständiges V ihrer Matrixzeilen.
- **Jetzt – R06-Produktentwicklung:** [#355](https://github.com/nauen/adventure_studio/pull/355), native Actor-Walkbox-Führung. [Head f6b8966](https://github.com/nauen/adventure_studio/commit/f6b896687a9a6ecad7867a664b3b11afcb9e4e49) ActorWalkboxModeStep in Modell/JSON-v1/Studio, nativer ScummC `setActorFollowBoxes`/`setActorIgnoreBoxes`, Anwesenheitsguard. Beide Operationen setzen forceClip zurück; beim Escape wird der letzte Modus vor Positions-/expliziten Clipping-Aktionen hergestellt. Kein eigener Pathfinding-Code. [Core](https://github.com/nauen/adventure_studio/actions/runs/45998480705) und [Native](https://github.com/nauen/adventure_studio/actions/runs/45998491088) gestartet. Abnahme: begrenzte native Gehfläche bis X=370, Ziel X=440, begrenzter Lauf → freier Lauf → nach Escape wieder begrenzt; jeweils stabile Positionsmessung. Noch kein Gameplay-Nachweis. Zusammenspiel mit offenem #329 manueller Skalierung bei Integration prüfen.
- **Offene Integration #353:** native Actor-Palettenzuordnung, Head 52bdc81, [Core](https://github.com/nauen/adventure_studio/actions/runs/45995777960) grün, [ScummVM-Artefakt 15195927049](https://github.com/nauen/adventure_studio/actions/runs/45995788559/artifacts/15195927049) ausgewertet: Original 672/0, Farbwechsel 0/672, nach Escape 672/0 Pixel, 0,349 s, `native_actor_palette_verified=true`. [Gesamtgate](https://github.com/nauen/adventure_studio/actions/runs/45995788559) läuft. Gleichfarbige lokale COST-Slots können zusammenfallen, Zielindex ist raumbezogen; 255 stellt Original wieder her.
- **Offene Abnahme #352:** nativer Laufstopp; Head 0532cc2, [Core 45995852466](https://github.com/nauen/adventure_studio/actions/runs/45995852466) grün, [Native 45995860389](https://github.com/nauen/adventure_studio/actions/runs/45995860389) Actor-Shard vor erster Interaktion rot: Startposition nicht erkannt. [Artefakt 15195444513](https://github.com/nauen/adventure_studio/actions/runs/45995860389/artifacts/15195444513) zeigt quantisierte Farbe 246/36/115 statt 242/38/117; exakter Farbvergleich ergibt 0 Pixel. [Head b6424e1](https://github.com/nauen/adventure_studio/commit/b6424e18e5ae9912fb16decfb6ec3ed45b22facc) korrigiert die Probe (Toleranz ±7, Szenenausschnitt, explizites BOXD, Ego getrennt). [Core](https://github.com/nauen/adventure_studio/actions/runs/45998543828) gestartet. [Native](https://github.com/nauen/adventure_studio/actions/runs/45998551752) gestartet. Kein Gameplay-Nachweis.
- **Offene Integration #350:** native Actor-Zeichenebene, Head 996f2a5, Core 45994504588 grün. [ScummVM-Artefakt 15195418170](https://github.com/nauen/adventure_studio/actions/runs/45994511162/artifacts/15195418170) ausgewertet: initial 0/672, vorne 672/0, nach Escape 0/672 Pixel; 0,349 s Escape, `native_actor_layer_verified=true`. [Gesamtgate](https://github.com/nauen/adventure_studio/actions/runs/45994511162) läuft. Keine universelle Sortiersemantik über SCUMM-Spielvarianten hinaus.
- **Offene Abnahme #348 (R07):** Head 3104bdd, [Core 45991898153](https://github.com/nauen/adventure_studio/actions/runs/45991898153) grün. [Native Mask 140482936603](https://github.com/nauen/adventure_studio/actions/runs/45991905870/job/140482936603) erreichte sichtbares IM01, brach vor erstem Zustandswechsel ab (Klickziel nicht gefunden, Sprite-Bounds 1x1-1-1). [Artefakt 15194406258](https://github.com/nauen/adventure_studio/actions/runs/45991905870/artifacts/15194406258). Keine IM03-Abnahme; IM03/ZP01 zurückgestellt. PNG deckend, vorhandene Raumpalette, Story-Erhalt.
- **Offene Abnahme #338:** Sprechfarbe/Position, Head bf598b5, [Core 45991670283](https://github.com/nauen/adventure_studio/actions/runs/45991670283) grün. Native Actor-Shard 140481050381: erste gewünschte Untertitelfarbe nicht beobachtet; [Artefakt 15193599646](https://github.com/nauen/adventure_studio/actions/runs/45991678190/artifacts/15193599646). Separater Chrome-Dialogpose-Fehler im selben Gesamtlauf; kein V. Kombination nach Transfer nicht nativ abgenommen.
- **Offene Integration #332:** Head dd27d8e, [Core 45990332397](https://github.com/nauen/adventure_studio/actions/runs/45990332397) grün, native Animationsgeschwindigkeitsprüfung erfolgreich ([Artefakt 15193288941](https://github.com/nauen/adventure_studio/actions/runs/45990343447/artifacts/15193288941)); [Gesamt-CI](https://github.com/nauen/adventure_studio/actions/runs/45990343447) läuft.
- **Konsolidierung #326–#331:** Die fünf Produktprüfungen Voice, Elevation, Scale, Costume und Walk Speed sind auf gemeinsamem #331-Head addbb41 im [aktuellen Native/Studio-Lauf 45987279728](https://github.com/nauen/adventure_studio/actions/runs/45987279728) erfolgreich, samt Artefakten [Voice 15192293539](https://github.com/nauen/adventure_studio/actions/runs/45987279728/artifacts/15192293539), [Elevation 15193211438](https://github.com/nauen/adventure_studio/actions/runs/45987279728/artifacts/15193211438), [Scale 15192303373](https://github.com/nauen/adventure_studio/actions/runs/45987279728/artifacts/15192303373), [Costume 15192811697](https://github.com/nauen/adventure_studio/actions/runs/45987279728/artifacts/15192811697), [Walk Speed 15192237987](https://github.com/nauen/adventure_studio/actions/runs/45987279728/artifacts/15192237987). Core auf den fünf jeweiligen Heads grün. Gesamtgates überwiegend laufend; #329 Gesamt-CI rot: nativer Kamera-Rendezvous-Test (Actor-Lanes X=395) und Chrome-NPC-Dialogpose. Keine Abschwächung; kein Merge oder vollständiges V vor Abnahme. Restore-Profile-Regression auf aktuellen Heads noch nicht abschließend verifiziert.
- **Offene Integration:** #326 Head cb16862 ([Native](https://github.com/nauen/adventure_studio/actions/runs/45986010446)); #328 Head 5e52cb2 ([Native](https://github.com/nauen/adventure_studio/actions/runs/45986061457)); #329 Head 0819d3f ([Native](https://github.com/nauen/adventure_studio/actions/runs/45986072883)); #330 Head 1fa9f09 ([Native](https://github.com/nauen/adventure_studio/actions/runs/45986089854)); #331 Head addbb41 ([Native](https://github.com/nauen/adventure_studio/actions/runs/45987279728)). #326 Abwesenheits-Gegenprobe grün; #329 manuelle Skalierung deaktiviert Walkbox-Führung, beide Moduswechsel setzen Z-Clipping zurück; Automatik-Rückkehr im Exporttest, nicht separat durch natives Bewegungsverhalten belegt.
- **Reihenfolge (Nutzerentscheidung 27.11.):** Nicht auf laufende CI warten, sondern genau das nächste produktive native R06-Paket bearbeiten; vorherige Pakete als offene Abnahme führen. Merge nur nach den unveränderten Pflichtgates und in Abhängigkeitsreihenfolge. #293/#295/#297/#299/#301/#303, #336, #339–#343 bleiben bis zur Priorisierung zurückgestellt; Branches erhalten. ZP05+ bleibt fail-closed.
- **Danach:** genau ein natives R06-Folgepaket nach Sichtung der bestehenden Produktpfade priorisieren; vor weiteren Kombinationen den offenen Z-Clipping-/Walkbox-Endzustandsvertrag konsolidieren. R07/IM03-ZP01 bleibt bis IM03-Abnahme zurückgestellt.

## Historischer Integrationsstand (26.11.2026) – nicht aktive Paketauswahl

- **Integriert (26.11.2026):** R06 [#314](https://github.com/nauen/adventure_studio/pull/314), native Wiederherstellung raumspezifischer Actor-Z-Clipping-Profile in regulären und per Escape abgeschlossenen Interaktionen; maskierte und transparente Kontrolle in stock ScummVM bestanden. Merge `459a51ab6a5738d989e37a0334f13df941e0044b`, [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45785194352) vollständig grün, [Authoring-Guard](https://github.com/nauen/adventure_studio/actions/runs/45785192359) grün; Core übersprungen.
- **Integriert (26.11.2026):** R06 [#320](https://github.com/nauen/adventure_studio/pull/320), native Actor-Bewegung nach Raumwechsel mit Clipping-Kontrolle in stock ScummVM bestanden; [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45803967171) 8/8 grün, Schritte 78/79 Gameplay und Evidenz erfolgreich. Merge `18f95154bfec1aaf6a6ed5b5dc9bfce8c42ab2b0`.
- **Integriert (26.11.2026):** R06 [#321](https://github.com/nauen/adventure_studio/pull/321), native Aktionsanimation eines übertragenen Actors im Zielraum in stock ScummVM bestanden; [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45821006309) 8/8 grün nach erfolgreicher Geometry-Wiederholung, Schritte 80/81 Gameplay und Evidenz erfolgreich. Merge `3bdb2b3131e8497527fe8eb72463f081dfa0973d`.
- **Integriert:** R06 [#313](https://github.com/nauen/adventure_studio/pull/313), dynamisches Z-Clipping nach Raumtransfer inklusive Escape und Redraw; Merge `20b2c07bca2d0187a8133c614bbe39422409013f`; [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45749196708) alle acht relevanten Shards grün, Geometry-Schritt 74 erfolgreich. R06 bleibt V (Teil).
- **Zurückgestellt:** #293/#295/#297/#299/#301/#303. Branches erhalten; ZP05+ fail-closed; R06 bleibt V (Teil).

- **Integriert:** [#312](https://github.com/nauen/adventure_studio/pull/312), Zielraumprofile nur für anwesende Actors, Merge `00d391fa69fde03e6a80db9faccfa4de4e4812ee`; [Core](https://github.com/nauen/adventure_studio/actions/runs/45538837093) und [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45538842077) erfolgreich; [Gameplay-Artefakt](https://github.com/nauen/adventure_studio/actions/runs/45538842077/artifacts/14992198888).
- **Integriert:** [#311](https://github.com/nauen/adventure_studio/pull/311), wiederverwendbare Actor-Z-Clipping-Profile, Merge `9dbcb2a1870f5920a1ffe1d577a118b2dfdb6223`; [Core](https://github.com/nauen/adventure_studio/actions/runs/45523680607) und [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45523686686) erfolgreich; [Gameplay-Artefakt](https://github.com/nauen/adventure_studio/actions/runs/45523686686/artifacts/14987105233). R06 bleibt V (Teil).
- **Integriert:** R08 [#264](https://github.com/nauen/adventure_studio/pull/264) konkaver Korridor, R09 [#267](https://github.com/nauen/adventure_studio/pull/267) zwei reversible Gates über Raumrückkehr; beide Teilfähigkeiten, keine vollständige Matrixfreigabe.

- **Integriert:** #327 Core-Testvertrag, Merge `7ee9aee`, Main-Core grün; keine Runtimeänderung.
- **Zurückgestellt:** #323/#325/#326 sowie die älteren gestapelten R06-Proben; keine parallele Featureentwicklung.

## Letzter integrierter Nachweis

- **Integriert:** R06 [#310](https://github.com/nauen/adventure_studio/pull/310), native Actor-Raumtransfers mit Zielposition und Z-Clipping, Merge `d9be9e58541b3915c32cf1e600930d4bad93d8d1`. [Core](https://github.com/nauen/adventure_studio/actions/runs/45510002671), [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45510010732) vollständig erfolgreich; [Transfer-Gameplay](https://github.com/nauen/adventure_studio/actions/runs/45510010732/artifacts/14980236628), [Retarget-Fix-Evidenz](https://github.com/nauen/adventure_studio/actions/runs/45510010732/artifacts/14976034924). R06 bleibt V (Teil).

- **Integriert:** R06 [#309](https://github.com/nauen/adventure_studio/pull/309), optionale Wiederherstellung der initialen Actor-Z-Ebene bei Raumrückkehr, Merge `f0c9e6ba8eac0fee344e976be59e72a6997862e8`. [Core](https://github.com/nauen/adventure_studio/actions/runs/45480583758), [Native/Studio](https://github.com/nauen/adventure_studio/actions/runs/45480592832) inklusive aller vier nativen Shards und Room-Return-Verify/Upload erfolgreich; [Gameplay-Evidenz](https://github.com/nauen/adventure_studio/actions/runs/45480592832/artifacts/14968500852). [Main-Core](https://github.com/nauen/adventure_studio/actions/runs/45499313071) grün. #306/#308 bleiben integriert; R06 bleibt V (Teil).


## Historische Roadmap-Stände – nicht aktive Arbeitsanweisungen

### Vorheriger Integrationskopf (abgeschlossen)

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime; Studio/JSON-v1/Story → ScummC-v6 → unverändertes stock ScummVM. Kein NPC-Komfort nach #190.
- **Integriert:** #289 (R06/#288, native Kamera übernimmt bereits laufenden Actor B nach Inspektionsfahrt), Merge `07447b59c7071eddc8c179cd94548dc20f9bc319`, [Native-CI 45271886275](https://github.com/nauen/adventure_studio/actions/runs/45271886275) alle vier Shards grün, [Gameplay-Artefakt](https://github.com/nauen/adventure_studio/actions/runs/45271886275/artifacts/14868911102); [Main-Core 45287621440](https://github.com/nauen/adventure_studio/actions/runs/45287621440) grün. R06 bleibt V (Teil); R08 #264 und R09 #267 sind ebenfalls integrierte Teilfähigkeiten.
- **Jetzt – genau eine Fähigkeit:** [#290 / PR #291](https://github.com/nauen/adventure_studio/pull/291), Actor B während des laufenden Walks ohne WaitActor auf ein neues natives Ziel umlenken. PR gegen main, Head `b538de018c54896d0e4d716e30dfc69cffbe7ffb`.
- **Abnahme:** Nach echtem stationärem Kamera-Rundgang mindestens drei native Links- und drei Rechtsbewegungs-Frames mit Umkehr und mindestens 90 Weltpixel rechtsgerichteter Weiterfahrt, drei unabhängig exportierte masked/transparent/wrong-box-Spiele; kein Teleport, keine Lockerung bestehender Masken-/Walkbox-Gates. Der PR ergänzt Probes/Tests/CI, keinen neuen allgemeinen Modell- oder Writer-Pfad; der Nachweis vorhandener nativer WalkActor-Komposition ist nicht automatisch eine neue authorierbare Produktfähigkeit.
- **Blocker/Nachweis (24.11.2026):** [Core 45287762974](https://github.com/nauen/adventure_studio/actions/runs/45287762974) grün; [Native 45287770846](https://github.com/nauen/adventure_studio/actions/runs/45287770846) Actor/Mask/Story grün, Retarget-Gameplay-Schritt und Artefakt-Upload im Geometry-Shard grün ([Artefakt 14875277048](https://github.com/nauen/adventure_studio/actions/runs/45287770846/artifacts/14875277048)); Geometry-Gesamtgate noch laufend. Kein Merge und keine zusätzliche V-Freigabe vor vollständigem finalem Gate.
- **Danach – genau ein Folgepaket:** #293 (beide Actors während des Walks umlenken) nur nach #291-Integration und Prüfung, ob dies eine tatsächlich noch offene Produktfähigkeit oder lediglich erneute Kombination bereits belegter Primitive ist. Keine weitere Probe ohne konkrete offene Abnahme. #295 → #297 → #299 → #301 → #303 bleiben zurückgestellt; alte Native-Runs dieser fünf PRs rot, #293 alter Native-Run grün, aber nicht auf aktualisierter Basis. ZP05+ bleibt fail-closed.


## Roadmap-Steuerung – aktuelles Einzelpaket (2026-11-23)

- **Hauptziel:** vollständiger nativer SCUMM-v6-Generator. Abnahme ausschließlich durch echtes Verhalten im unveränderten ScummVM und passende Pflicht-CI.
- **Bereits integriert:** #266 (R06 Masken/Bewegung), #264 (R08 konkaver Walkbox-Korridor), #267 (R09 reversible Gates) und #269 (R06 zwei unabhängig bewegte Actors, Issue #268).
- **Jetzt = 1 Fähigkeit:** R06 [#270](https://github.com/nauen/adventure_studio/issues/270) / offener [PR #271](https://github.com/nauen/adventure_studio/pull/271). Kamera folgt Actor A, übergibt während überlappender Actor-Bewegung an Actor B und fährt zurück; vier ZP01–ZP04 bleiben weltfest, alle acht Actor-Maskenpaare gegen transparente/Wrong-BOXD-Kontrollen nachweisen.
- **Abnahme:** echtes Studio/JSON-v1/Story → produktiver ScummC-v6-Export → drei unabhängig gelinkte Spiele → native zeitgestempelte ScummVM-Screenshots, unabhängige Actor-Weltpositionen, messbare Fokusübergabe, Kamerarückweg, acht Z-Maskenkontrollen und vollständige Core-/Native-Pflicht-CI auf finalem Head. Alter Gameplay-Beleg [45088766893](https://github.com/nauen/adventure_studio/actions/runs/45088766893) ist keine Merge-Freigabe.
- **Aktueller Blocker:** fehlgeschlagene Core-/Geometry-/Story-Gates auf Head fd278018 (Runs 45090596656 und 45090602659), gezielte Fix-Commits auf dem bestehenden PR-Branch gepusht. Bis aktuelle grüne CI vorliegt: **nicht mergen, kein neues Paket**.
- **Danach = 1 Folgepaket:** erst nach #271-Abnahme genau eine offene native Matrixlücke nach Nutzerwert und Abhängigkeiten auswählen; kein NPC-Komfort, keine ZP05+-Unterstützung behaupten.

## Historische Roadmap-Stände (keine aktuelle Paketreihenfolge)


## Aktueller integrierter Stand und nächste native Abnahme (2026-11-22)

- **R06:** PR #266, native laufende Actor-Route über vier weltfeste ZP01–ZP04-Masken und vollständige Kamerarückfahrt, integriert.
- **R08:** PR #264, konkaver L-förmiger Korridor aus verbundenen nativen Walkboxes, integriert.
- **R09:** PR #267, zwei reversible native Walkbox-Gates einschließlich Raumwechsel und Rückkehr, integriert mit vollständiger nativer CI #45064059570 und Merge `b5c7cc28`.
- **Jetzt aktiv:** R06 Folgepaket [#268](https://github.com/nauen/adventure_studio/issues/268): zwei voneinander unabhängige bewegte Actors hinter vier weltfesten Raum-Z-Masken im selben stock-ScummVM-Spiel. **Noch nicht implementiert oder abgenommen.** ZP05+ bleibt ausdrücklich fail-closed.


## Konsolidierung und unmittelbar gestartetes R06-Folgepaket (2026-11-22)

- **Hauptziel:** vollständiger nativer SCUMM-v6-Generator ohne Zusatzruntime.
- **Integriert:** R06 PR #262 (`128c9ff`) mit vier gleichzeitigen weltfesten ZP01–ZP04-Masken und nativer Kamerafahrt; R06 bleibt insgesamt Teilfähigkeit.
- **Offene Integration:** R09 PR #260 (Story-Pflichtgate nach R06-Integration laut PR noch rot), R08 PR #264 (L-Korridor, echte Actor-Knickroute und finale Pflicht-CI noch offen). Keine dieser Teilfähigkeiten als fertig oder gemergt ausgeben.
- **Jetzt, explizit priorisiert:** genau ein neues natives R06-Paket [#265](https://github.com/nauen/adventure_studio/issues/265): laufender Actor durch alle vier Masken während Kamera-Hin-/Rückfahrt. Die vorherigen getrennten Actor-Standpositionen nicht als Bewegungsnachweis umdeuten.
- **Abnahme:** echtes Studio → JSON-v1/Story → ScummC/BOXD/BOXM → unverändertes ScummVM; gemessene Actor-/Kamerapositionen, unabhängige transparente und Wrong-Box-Kontrollen, Screenshots/Logs/Report, grüne Core-/Chromium-/Native-Pflichtgates.
- **Blocker/Nicht-Ziele:** kein belegter neuer Gameplay-Nachweis für #265; R09/R08-Merge-Gates bleiben offen; ZP05+ stock-v6 fail-closed; kein NPC-Komfort.
- **Danach:** erst #265 vollständig nativ abnehmen und offene Integrationsgates klären, dann genau ein Folgepaket wählen.


Stand: 2026-11-22. Nur die nächste Produktentscheidung wird hier gesteuert;
die einzige 64-Fähigkeiten-Matrix ist [SCUMM_V6_CAPABILITIES](SCUMM_V6_CAPABILITIES.md).

## Aktiver Entscheidungsstand

- **Hauptziel:** Vollständiger nativer SCUMM-v6-Generator ohne zusätzliche Adventure-Studio-Runtime.
- **Jetzt:** **R06 / [Issue #261](https://github.com/nauen/adventure_studio/issues/261), [PR #262](https://github.com/nauen/adventure_studio/pull/262)**: vier gleichzeitig authorierte Raum-Z-Masken ZP01–ZP04 plus fünf Walkboxen bleiben bei nativer Kamerafahrt X=160→480→160 weltfest. Keine NPC-Komfortarbeit seit #190; kein paralleles R07/R08/R09-Paket.
- **Abnahme:** Vier echte Studio-PNGs → RoomAsset/JSON-v1/Story → produktiver ScummC-v6-/BOXD-Export → **zwölf separat kompilierte Spiele** in unverändertem stock ScummVM (für jede Z-Ebene: maskiert, transparent, falsche Walkbox). Jede Ebene muss den Actor auf Hin- und Rückfahrt verdecken; beide Kontrollen müssen ihn zeigen, der vollständige Kamera-Rückweg muss beobachtet werden. Native Logs, JSON-Report, Screenshots und Browser-Authoring-Evidenz als Artefakte.
- **Blocker:** [Native 45019052534](https://github.com/nauen/adventure_studio/actions/runs/45019052534) hat **alle zwölf echten stock-ScummVM-Spiele** kompiliert, gestartet und mit Zeitstempeln dokumentiert: ZP01–ZP03 je 0 verdeckte Actor-Pixel, ZP04 296 gegenüber 1540 in beiden Kontrollen, jeweils auf Hin-/Rückfahrt. [Artefakt](https://github.com/nauen/adventure_studio/actions/runs/45019052534/artifacts/14752699463). Das abschließende CI-Gate war trotzdem rot, weil der statische Start-/Endbild-Vergleich `scroll_color_signature_passed` bei beabsichtigter X=160→480→160-Rückkehr definitionsgemäß falsch ist (`scroll_expected=false`). Der Selektor verlangt jetzt **echte Frame-Variation plus gemessenen vollständigen Kameraverlauf**; der separate ZP01-Basistest berücksichtigt den belegten 32er-Kamera-Samplingversatz. Finales Core/Native/Studio-Gate nach dem Fix noch offen. ZP05+ bleibt stock-v6-fail-closed.
- **Danach:** Erst nach R06-ScummVM-Nachweis und grünen Pflichtgates das einzelne R09-Walkbox-Raumrückkehrpaket [PR #260](https://github.com/nauen/adventure_studio/pull/260) konsolidieren und abnehmen. Keine anderen parallelen Features.

## Grundlagen – nicht erneut als Neuimplementierung einplanen

| Historisches Paket | Tatsächlicher Teilstand | Noch fehlender Abschluss |
| --- | --- | --- |
| P0.1 – Raum-Binärprüfung | Chunk-/Offset-Parser und deterministische Tests vorhanden | Allgemeinheit und noch nicht abgedeckte Binärvarianten separat prüfen |
| P0.2 / R06 – Z-Masken | Studio/JSON/Story-ZP01 bis ZP04 mit Walkbox-Zuordnung und jeweils getrennter Actor-Verdeckung in stock ScummVM nachgewiesen; PR #198/#204/#208, native Runs `43105298694`, `43251867709`, `43264467363` | ZP05 scheitert in stock ScummVM; ungemergter PR #216 als Negativbefund geschlossen. PR #218 verweigert ZP05+ vor Asset-Erzeugung und erhält Studio-Daten; PR #220 beweist zwei, PR #222 drei verschiedene Masken gleichzeitig über benachbarte Walkboxen und Rückweg; vier gleichzeitig seit #224 nativ mit Rückweg belegt; darüber hinausgehende Kombinationen und ZP05+ bleiben offen |
| P0.3 / R08–R10 – Walkbox/SCAL | `RoomAsset.walkboxes`, BOXM, SCAL, JSON und native Sicht-/Skalierungsprobe; R08.1 konvexe Box und R09 Vier-Boxen-Alternativen, Fünf-Boxen-T-Netz und zyklisches Sechs-Walkbox-Netz mit beiden Ausweichrouten bis stock ScummVM belegt | Allgemeine Polygone, größere/mehrfach dynamische Boxennetze und Perspektivvarianten offen; einmalige Tür-Abkürzung #226, reversibles Gate #229, natives Save/Load #230, zwei Räume #232 und zwei unabhängige Gates im selben Raum #236 belegt |
| P0.5 / A01–A07 – Actors/Costumes | COST, Framefolgen, COUNT und viele Gameplay-Teilproben vorhanden | Alle Actor-/Costume-Varianten und native Mehrsprecher-Animation noch nicht fertig |

Diese Teilstände ergeben sich aus
[`scumm_assets.py`](../src/adventure_studio/scumm_assets.py),
[`scumm_project.py`](../src/adventure_studio/scumm_project.py),
[`test_scumm_room_primitives.py`](../tests/test_scumm_room_primitives.py)
und den nativen Szenarien in
[`scummc-experiment.yml`](../.github/workflows/scummc-experiment.yml).
Die [Funktionsmatrix](SCUMM_V6_CAPABILITIES.md) benennt je ID die
unvollständigen Stufen. Ein grüner Fixture-Test ist keine universelle
SCUMM-v6-Abdeckung.

## Verbindliche Produktreihenfolge

1. **P1:** Vollständiger originaler nativer SCUMM-v6-Generator;
   keine zusätzliche Adventure-Studio-Runtime.
2. **P2:** Durchgängiger visueller Editor für die unterstützten nativen Daten.
3. **P3:** Filmischer Shot-/Cutscene-Editor auf belegten nativen Primitiven.
4. **P4:** KI-gestützte und überprüfbare Erstellung.
5. **P5:** Produktreife und Distribution.

## Freigaberegel pro Paket

1. Nutzerverhalten, Capability-ID und 0/1/2/N-Grenzen benennen.
2. Modell → Export → deterministische Tests implementieren.
3. Bei Gameplay die konkrete Wirkung im unveränderten ScummVM prüfen;
   bei Blockade exakt den fehlenden Nachweis nennen.
4. Core-, passende UI- und native CI abnehmen; nur grün und autorisiert mergen.
5. **Nur diese Roadmap, den aktuellen Status und die betroffenen
   Matrixzeilen aktualisieren.** Historische Nachweise bleiben im Archiv.

Ein offenes altes Paket wird nicht stillschweigend als fertig markiert;
eine klar abgegrenzte Teilabnahme ist zulässig, aber nicht dasselbe
wie vollständige native Feature-Unterstützung.
