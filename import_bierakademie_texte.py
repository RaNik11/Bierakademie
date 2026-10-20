# -*- coding: utf-8 -*-
"""Bierakademie: 195 Kurzgeschmaecker und Beschreibungen.

SPEICHERN: Neben manage.py als import_bierakademie_texte.py.

TEST OHNE AENDERUNG:
    python import_bierakademie_texte.py

TATSAECHLICHER IMPORT:
    python import_bierakademie_texte.py --apply

BESTEHENDE TEXTE ERSETZEN (NUR WENN GEWOLLT):
    python import_bierakademie_texte.py --apply --overwrite

Sicherungen werden vor jedem Schreibzugriff automatisch erstellt.
Preise, Bilder, Herstellertexte und Sichtbarkeit bleiben unveraendert.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# id|exakter Produktname aus dem bereitgestellten JSON|Kurzgeschmack|2 Saetze Beschreibung
DATA = r"""
1|Hefe|Hefe · mild · fruchtig|Ein naturtrübes Hefeweizen aus München mit weichem, frischem Charakter. Die typische Weizenbiernote macht es zu einem unkomplizierten Klassiker vom Fass.
2|Gold, Halbe|Hell · mild · süffig|Ein helles Bier aus Wurmlingen mit angenehm mildem Geschmack. Frisch gezapft überzeugt die Halbe durch ihren ausgewogenen, süffigen Charakter.
3|Pils|Frisch · herb · hopfig|Ein klassisches Pils aus Bitburg mit deutlicher Hopfennote. Seine feinherbe Frische macht es zu einer beliebten Wahl vom Fass.
4|Russ Mixbier|Weizig · spritzig · erfrischend|Beim Russ trifft Hefeweizen auf eine spritzige Zugabe, wahlweise süß oder sauer. So entsteht ein erfrischendes Biermischgetränk mit dem typischen Charakter von Weißbier.
5|Radler Mixbier|Mild · spritzig · erfrischend|Eine Mischung aus hellem Bier und einer spritzigen Zugabe, wahlweise süß oder sauer. Das Radler schmeckt erfrischend und angenehm leicht im Vergleich zum puren Hellen.
6|Cola Weizen Mixbier|Malzig · süß · Cola|Weißbier und Cola verbinden sich zu einem süßlich-würzigen Biermischgetränk. Fruchtige Weizenbiernoten treffen auf den unverwechselbaren Geschmack der Cola.
7|Original|Hell · rund · malzig|Das Original von Gold Ochsen steht für Ulmer Bierkultur. Ein helles Bier mit ausgewogenem, angenehm vollmundigem Charakter.
8|Helles|Mild · ausgewogen · süffig|Ein helles Lagerbier von Benediktiner mit sanftem, ausgewogenem Geschmack. Sein unkomplizierter Charakter passt besonders gut zu einer gemütlichen Brotzeit.
9|Helles|Mild · weich · süffig|Das Hirsch Helles aus Wurmlingen ist auf unkomplizierten Biergenuss ausgelegt. Es schmeckt mild und angenehm süffig.
10|Bügel Premium|Frisch · süffig · mild|Ein erfrischendes Bier aus Stuttgart in der traditionellen Bügelflasche. Sein süffiger Charakter macht es zu einem angenehmen Begleiter für gesellige Abende.
11|Edelstoff|Malzig · vollmundig · harmonisch|Augustiner Edelstoff ist ein klassisches Münchner Exportbier. Seine ausgewogene Art verbindet vollmundigen Biergeschmack mit angenehmer Frische.
12|Hefe TAP 1|Weizig · mild · harmonisch|Die helle Weißbierspezialität TAP 1 von Schneider stammt aus Kelheim. Bayerische Reifetradition und ein harmonischer Hefeweizencharakter stehen hier im Vordergrund.
13|Original TAP 7|Naturtrüb · würzig · rund|Schneider Original TAP 7 ist ein charaktervolles, naturtrübes Weißbier aus Kelheim. Sein etwas dunklerer Farbton unterstreicht den traditionellen Weizenbierstil.
14|Hefe|Naturtrüb · mild · frisch|Ein klassisches Paulaner Hefe-Weißbier mit natürlicher Hefetrübung. Sein weicher, frischer Charakter macht es zu einem beliebten Münchner Bierklassiker.
15|Hefe Original|Goldgelb · weich · weizig|Das Huber Hefe Original präsentiert sich goldgelb im Glas. Ein traditionelles Weißbier mit angenehm weichem Weizenbiercharakter.
16|Hefe|Weizig · frisch · harmonisch|Ein bayerisches Hefeweizen aus Erding mit dem typischen Charakter naturtrüber Weißbiere. Seine lebendige Frische sorgt für unkomplizierten Genuss.
17|Hefe|Naturtrüb · weich · weizig|Franziskaner Hefe ist ein klassisches naturtrübes Weißbier aus München. Es verbindet weichen Weizenbiergeschmack mit erfrischendem Charakter.
18|Zwickl Unfiltriert|Naturtrüb · ursprünglich · mild|Dieses unfiltrierte Zwickl aus Wurmlingen bewahrt seine natürliche Trübung. Eine bodenständige Bierspezialität für alle, die ursprüngliches Bier mögen.
19|Kristall TAP 2|Kristallklar · spritzig · frisch|Schneider Kristall TAP 2 ist ein klares Weizenbier aus Kelheim. Ohne die typische Hefetrübung zeigt es eine besonders spritzige, erfrischende Seite des Weißbiers.
20|Kristall|Klar · lebendig · spritzig|Das Erdinger Kristall ist die klare Variante des bekannten Weißbierstils. Seine lebendige Kohlensäure macht es besonders erfrischend.
21|Kristall|Kristallklar · frisch · leicht|Sanwald Kristall ist ein klar filtriertes Weizenbier aus Stuttgart. Ein spritziger Weißbiergenuss ohne Hefetrübung.
22|Kristall|Klar · feinperlig · frisch|Ein kristallklares Weizenbier aus Freising mit lebendigem Charakter. Seine klare Erscheinung und spritzige Frische machen es zu einer Alternative zum Hefeweizen.
23|Kristall|Klar · prickelnd · frisch|Maisel's Kristall steht für prickelnde Weizenbierfrische aus Bayreuth. Das klare Bier verbindet typischen Weißbiercharakter mit lebendiger Kohlensäure.
24|Brunnenbier|Naturtrüb · mild · regional|Das Gruibinger Brunnenbier ist eine naturtrübe Spezialität aus der Region. Ein bodenständiges Bier für alle, die ursprünglichen Genuss schätzen.
25|Tannenzäpfle Pils|Feinherb · hopfig · frisch|Das Tannenzäpfle ist ein Pils-Klassiker aus dem Schwarzwald. Eine frische, feinherbe Hopfennote prägt seinen charakteristischen Geschmack.
26|Pils|Herb · hopfig · trocken|Jever Pils steht für den markanten friesisch-herben Bierstil. Deutliche Hopfenbittere und ein trockener Eindruck zeichnen dieses Pils aus.
27|Pils|Frisch · herb · klar|Beck's Pils ist ein klassischer Pilsgenuss aus Bremen. Der Geschmack ist frisch, klar und angenehm herb.
28|Goldstoff Bügelflasche|Mild · zart hopfig · süffig|Hirsch Goldstoff aus Wurmlingen kommt in der traditionellen Bügelflasche. Sein ausgewogener Charakter wird von einer zarten Hopfennote begleitet.
29|Bügelflasche|Mild · malzig · frisch|Wulle aus Stuttgart steht für bodenständigen Biergenuss in der Bügelflasche. Ein unkomplizierter Klassiker mit angenehm mildem Biercharakter.
30|Alt|Malzig · würzig · herb|Diebels Alt ist ein dunkleres Bier nach Altbier-Art aus Issum. Seine malzige Würze mündet in einen angenehm charaktervollen Abgang.
31|Pilsner|Klar · feinherb · hopfig|König Pilsener ist ein klassisches Pils aus Duisburg. Eine klare Hopfennote und feinherbe Frische prägen den Geschmack.
32|Original|Spritzig · süßlich · Tequila-Aroma|Desperados Original verbindet Bier mit einem auffälligen Tequila-Aroma. Das Ergebnis ist ein spritziges Biermischgetränk mit süßlich-würzigem Charakter.
33|Dunkel|Dunkel · malzig · hefetrüb|Franziskaner Dunkel ist ein hefetrübes, dunkles Weißbier aus München. Seine dunkle Malznote ergänzt den typischen Weizenbiercharakter.
34|Dunkel|Dunkelbraun · malzig · weich|Dieses dunkle Erdinger Weißbier zeigt sich mit tiefbrauner Farbe im Glas. Der weiche Weizenbiercharakter wird von dunkleren Malznoten begleitet.
35|Dunkel Hefe|Dunkel · mild · malzig|Das Hirsch Dunkel Hefe aus Wurmlingen ist ein dunkles Weißbier mit milder Hopfung. Seine Malznote steht im Vordergrund und sorgt für einen runden Eindruck.
36|Schottenbock|Kräftig · Whiskyfass · malzig|Der Schottenbock ist eine besondere Bierspezialität aus Gruibingen, die ein Jahr im Whiskyfass gereift ist. Die Fasslagerung bringt feine Whiskyaromen in den kräftigen Bockbiercharakter.
37|Premium Silver Label — Jahrgangsbieredition 2019|Kastanie · Holzfass · kräftig|Diese Hirsch-Jahrgangsedition von 2019 ist ein kastanienbraunes Bockbier. Neun Monate Lagerung im Madeira-Eichenfass verleihen der Spezialität ihren besonderen Fasscharakter.
38|Aventinus Eisbock|Würzig · Pflaume · Marzipan|Dieser dunkle Aventinus Eisbock begeistert mit intensiven, würzigen Pflaumennoten. Anklänge von Bittermandel und Marzipan verleihen ihm aromatische Tiefe.
39|Black Shark|Röstaromen · Kaffee · Frucht|Camba Black Shark verbindet fruchtige Eindrücke von Rhabarber, Stachelbeere und Pfirsich mit kräftigen Röstnoten. Kaffee und Bitterschokolade setzen dunkle Akzente.
40|Imperial IPA|Hopfig · Limette · Zitrus|Das Imperial IPA von Camba zeigt ausgeprägte Hopfenaromen mit Limetten- und Zitrusnoten. Eine kräftige, gut ausbalancierte Hopfenbittere sorgt für einen langen Eindruck.
41|Aventinus Doppelbock TAP 6|Kräftig · weizig · dunkel|Schneider Aventinus TAP 6 ist ein intensiver Weizendoppelbock mit dunkler Rubinfarbe. Seine kräftige Art macht ihn zu einer besonderen Weißbierspezialität.
42|Hopfenweiße TAP 5|Blumig · herb · malzsüß|Die Schneider Hopfenweiße TAP 5 verbindet ausgeprägte Aromahopfennoten mit der Fülle eines Weizendoppelbocks. Blumige Herbe trifft auf malzige Süße.
43|Doppelbock|Röstmalz · Dörrobst · weich|Der dunkle Doppelbock aus Andechs zeichnet sich durch weiche Röstnoten aus. Ein Hauch Dörrobst ergänzt seinen kräftigen, malzigen Charakter.
44|Bergbock Hell|Malzig · blumig · kräftig|Andechser Bergbock Hell präsentiert sich klar und goldfarben. Kräftige Malznoten und blumige Hopfenaromen machen ihn zu einem ausdrucksstarken hellen Bockbier.
45|Salvator|Bernstein · malzig · vollmundig|Paulaner Salvator ist ein bernsteinfarbener Doppelbock nach bayerischer Brautradition. Sein vollmundiger, malzbetonter Charakter macht ihn zu einem Klassiker unter den Starkbieren.
46|Korbinian|Malzig · fruchtig · kräftig|Weihenstephaner Korbinian ist ein dunkler Doppelbock mit feinen Malzaromen. Dezente fruchtige Nuancen begleiten den kräftigen Biergeschmack.
47|Hefe Alkoholfrei|Weizig · frisch · alkoholfrei|Schneider Hefe Alkoholfrei bietet den typischen Charakter eines Weizenbiers ohne die übliche Alkoholstärke. Laut Getränkekarte ist diese Variante isotonisch und vitaminhaltig.
48|Hefe Alkoholfrei|Weizig · mild · alkoholfrei|Das alkoholfreie Benediktiner Hefe bewahrt den milden Charakter eines Weißbiers. Eine erfrischende Wahl für alle, die auf Alkohol verzichten möchten.
49|0,0|Pilsfrisch · herb · 0,0 %|Bitburger 0,0 bietet eine alkoholfreie Alternative zum klassischen Pils. Im Vordergrund stehen erfrischender Biergeschmack und eine feinherbe Note.
50|Blue|Frisch · pilsartig · alkoholfrei|Beck's Blue ist die alkoholfreie Variante des Bremer Bierklassikers. Ein frischer, pilsartiger Geschmack sorgt für unkomplizierten Biergenuss.
51|Gentleman Jack|Weich · Vanille · Holz|Gentleman Jack ist ein Tennessee Whiskey mit besonders weichem Charakter. Sanfte Holz- und Vanilleeindrücke machen ihn zu einem runden Whiskeygenuss.
52|Nr. 7|Vanille · Eichenholz · würzig|Jack Daniel's Old No. 7 ist ein Tennessee Whiskey mit markantem Charakter. Würzige Holztöne und eine sanfte Vanillenote prägen den bekannten Klassiker.
53|Honey Whiskey|Honigsüß · weich · würzig|Wild Turkey Honey verbindet Whiskeycharakter mit einer süßlichen Honignote. Ein weicher Genuss für alle, die es aromatisch und weniger herb mögen.
54|95 Rye Frontier Whiskey|Roggen · würzig · trocken|Bulleit 95 Rye ist ein Rye Whiskey mit ausgeprägter Roggenwürze. Sein kräftiger, eher trockener Charakter hebt ihn von milden Bourbons ab.
55|Straight Bourbon|Vanille · Eiche · Karamell|Woodford Reserve Straight Bourbon ist ein amerikanischer Bourbon mit vollem Charakter. Klassische Bourbonnoten von Eiche, Vanille und Karamell stehen im Mittelpunkt.
56|Bourbon Whiskey|Karamell · Vanille · Eiche|Jim Beam Bourbon ist ein amerikanischer Whiskeyklassiker. Sein süßlich-würziger Geschmack zeigt typische Bourbonnoten von Vanille, Karamell und Holz.
57|Single Malt Whisky|Malzig · weich · fruchtig|SLYRS Single Malt ist eine bayerische Whisky-Spezialität. Sein malzbetonter, weicher Charakter wird von einer dezenten fruchtigen Seite begleitet.
58|Malt Whisky Sherry Single|Malzig · Sherry · mild|Dieser Tecker Malt Whisky trägt den Hinweis auf Sherry im Namen. Ein malziger Whisky für alle, die eine von Sherryfassnoten geprägte Stilrichtung schätzen.
59|Sherry Cask Matured Single Malt|Sherryfass · Malz · würzig|Dieser Tecker Single Malt wurde laut Produktbezeichnung im Sherryfass gereift. Die Kombination aus Malzcharakter und Fasswürze steht im Mittelpunkt.
60|Aged 5 Years|Malzig · Holz · gereift|Tecker Aged 5 Years ist ein Whisky mit ausgewiesener fünfjähriger Reifezeit. Eine malzige Spirituose mit charaktervoller Fassnote.
61|Peated Single Malt Whiskey|Rauchig · torfig · malzig|Connemara Peated Single Malt ist ein irischer Whiskey mit rauchig-torfigem Charakter. Die rauchige Seite verleiht dem malzigen Grundgeschmack besondere Tiefe.
62|Ireland's Legendary Honey Liqueur|Honig · Kräuter · süß|Irish Mist ist ein irischer Likör auf Whiskeybasis mit Honigcharakter. Kräuterige Noten ergänzen seine angenehme Süße.
63|Single Pot Still|Kräftig · würzig · malzig|Redbreast Single Pot Still steht für einen eigenständigen irischen Whiskey-Stil. Sein reichhaltiger, würziger Charakter bietet mehr Tiefe als ein besonders leichter Whiskey.
64|Single Malt Whiskey|Malzig · weich · rund|Bushmills Single Malt stammt aus der irischen Whiskeytradition. Er verbindet einen malzigen Grundcharakter mit einer angenehm weichen Art.
65|Original|Süß · fruchtig · würzig|Southern Comfort Original ist eine süßliche Spirituose mit fruchtigem und würzigem Charakter. Sie wird häufig pur oder als Bestandteil von Mixgetränken genossen.
66|Speyside Single Malt Whisky|Fruchtig · malzig · weich|Aberlour ist ein Single Malt aus der schottischen Speyside. Der Stil verbindet weichen Malzcharakter mit einer fruchtigen, warmen Aromatik.
67|Single Malt|Rauch · Pfeffer · Meersalz|Talisker Single Malt ist für seinen maritimen, würzigen Charakter bekannt. Rauchige Eindrücke, Pfefferwürze und eine salzige Anmutung ergeben ein kräftiges Profil.
68|Islay Single Malt|Intensiv · Torfrauch · würzig|Ardbeg Single Malt von der Insel Islay steht für ausgeprägte Rauchigkeit. Torf und kräftige Würze machen diesen Scotch zu einer markanten Wahl.
69|Single Malt|Malzig · würzig · dezent rauchig|Highland Park Single Malt stammt aus Schottland und verbindet Malznoten mit Würze. Eine dezente rauchige Seite gibt dem Whisky zusätzliche Tiefe.
70|The Isle of Skye Liqueur|Honig · Kräuter · würzig|Drambuie ist ein schottischer Likör auf Whiskybasis. Honigsüße und Kräuterwürze sorgen für einen aromatisch-warmen Geschmack.
71|Single Malt|Weich · malzig · fruchtig|Cardhu Single Malt steht für eine eher weiche schottische Whisky-Stilrichtung. Sein malziger Charakter wird von milden, fruchtigen Eindrücken begleitet.
72|Gold Label Reserve|Weich · Honig · Vanille|Johnnie Walker Gold Label Reserve ist ein Blended Scotch mit harmonischem Charakter. Sanfte Honig- und Vanilleanklänge machen ihn besonders rund.
73|Red Label Reserve|Würzig · malzig · leicht rauchig|Johnnie Walker Red Label gehört zu den bekannten Blended-Scotch-Klassikern. Sein lebendiger Geschmack verbindet Malzwürze mit leicht rauchigen Anklängen.
74|Blended Whisky|Weich · malzig · fruchtig|Chivas Regal ist ein schottischer Blended Whisky mit ausgewogenem Charakter. Eine sanfte Malznote trifft auf dezente fruchtige Süße.
75|Golden Selection Blended Whisky|Mild · malzig · würzig|Dimple Golden Selection ist ein schottischer Blended Whisky. Sein harmonischer Charakter vereint sanfte Malzigkeit mit milder Würze.
76|Finest Blended Whisky|Vanille · mild · malzig|Ballantine's Finest ist ein klassischer Blended Scotch. Weiche Malznoten und eine zarte Vanillesüße prägen seinen zugänglichen Geschmack.
77|Solera Gran Reserva|Karamell · Holz · süßlich|Ron Zacapa Solera Gran Reserva ist ein reichhaltiger Rum aus Guatemala. Sein runder Charakter erinnert an Karamell, süße Gewürze und Holzfassnoten.
78|Small Batch|Vanille · fruchtig · weich|Don Papa Small Batch ist ein Rum von den Philippinen. Seine weiche, süßlich-fruchtige Aromatik macht ihn zu einer charaktervollen Spezialität.
79|Gran Reserva|Holz · Vanille · rund|Matusalem Gran Reserva ist ein Rum im gereiften Stil. Eine weiche Aromatik mit Holz- und Vanilleanklängen steht im Vordergrund.
80|Coconut Rum|Kokos · tropisch · süß|Belmont Estate Coconut Rum verbindet Rumcharakter mit tropischem Kokosaroma. Eine süßliche Spezialität für alle, die Kokos mögen.
81|Elixir|Süß · Rosinen · karamellig|Legendario Elixir ist eine süßliche kubanische Rum-Spezialität. Vollmundige Noten von Rosinen und Karamell prägen ihren likörartigen Charakter.
82|Aged 7 Years|Weich · Vanille · Holz|Centenario Aged 7 Years ist ein gereifter Rum mit ausgewogenem Charakter. Vanille- und Holznoten sorgen für einen warmen, runden Eindruck.
83|Aniversario Reserva Exclusiva|Kräftig · Karamell · Holz|Pampero Aniversario Reserva Exclusiva ist ein gereifter venezolanischer Rum. Seine kräftige, warme Art verbindet Holzfasscharakter mit karamelliger Süße.
84|7 Years|Eiche · Vanille · würzig|Havana Club 7 Years ist ein gereifter kubanischer Rum. Holzfassnoten und eine warme Würze verleihen ihm einen markanten Geschmack.
85|3 Years|Frisch · Zuckerrohr · mild|Havana Club 3 Years ist ein heller kubanischer Rum. Sein klarer, leichter Zuckerrohrcharakter eignet sich auch für klassische Mixgetränke.
86|Rum (Sorte prüfen)|Rumtypisch · würzig · Sorte offen|Captain Morgan ist als Marke für Rum und Rum-Spezialitäten bekannt. Die genaue Sorte dieser Position ist noch nicht bestätigt; Geschmack und Zutaten können deshalb abweichen.
87|White Rum|Leicht · klar · Zuckerrohr|Bacardi White Rum ist ein heller Rum mit vergleichsweise leichtem Charakter. Er eignet sich pur oder als Grundlage zahlreicher klassischer Cocktails.
88|Rum 80|Intensiv · würzig · kräftig|Stroh 80 ist eine besonders hochprozentige österreichische Spirituosenspezialität. Das intensive, würzige Aroma ist deutlich kräftiger als bei gewöhnlichem Rum.
89|Grand Very Old|Rund · würzig · gereift|Metaxa Grand Very Old ist eine gereifte griechische Spirituosenspezialität. Ihr voller, aromatischer Charakter lädt zum langsamen Genießen ein.
90|7 Sterne|Fruchtig · weich · würzig|Metaxa 7 Sterne ist eine griechische Spirituose mit vielseitiger Aromatik. Weiche Fruchtnoten und warme Würze prägen den runden Geschmack.
91|3 Sterne|Vollmundig · mild · warm|Metaxa 3 Sterne ist eine griechische Spirituosenspezialität mit vollmundigem Charakter. Ihr harmonischer Geschmack verbindet milde Würze mit angenehmer Wärme.
92|Very Special|Eiche · würzig · kräftig|Hennessy Very Special ist ein Cognac mit ausgeprägtem Charakter. Warme Eichenholznoten und eine kräftige Würze prägen den Geschmack.
93|Uralt|Mild · Holz · warm|Asbach Uralt ist ein deutscher Weinbrand mit gereiftem Charakter. Die Fasslagerung verleiht ihm eine warme, holzbetonte Aromatik.
94|Weinbrand (Sorte prüfen)|Weich · rund · mild|Chantré Weinbrand ist für einen weichen, runden Geschmack bekannt. Eine milde Wahl für alle, die einen unkomplizierten Weinbrand suchen.
95|Gin|Wacholder · Kräuter · trocken|Gordon's Gin steht für einen klassischen trockenen Gin-Stil. Wacholder und würzige Kräuternoten stehen im Vordergrund.
96|Wodka|Klar · mild · neutral|Wodka Gorbatschow ist ein klassischer Wodka mit klarem Geschmacksbild. Sein vergleichsweise neutraler Charakter eignet sich pur oder für Mixgetränke.
97|Wodka (Roter)|Wodka · Sorte unbestätigt|Dieser rote Gorroff-Wodka wird in der gedruckten Karte als eigene Variante geführt. Die genaue Geschmacksrichtung ist nicht angegeben und sollte vor der Veröffentlichung bestätigt werden.
98|Wodka (Schwarzer)|Wodka · Sorte unbestätigt|Dieser schwarze Gorroff-Wodka wird als eigenständige Sorte angeboten. Welches Aroma sich hinter der Farbvariante verbirgt, ist noch zu klären.
99|Wodka (Grüner)|Wodka · Sorte unbestätigt|Der grüne Gorroff-Wodka ist laut Getränkekarte eine weitere Variante der Marke. Für eine präzise Geschmacksbeschreibung fehlt noch die genaue Produktbezeichnung.
100|Ouzo|Anis · würzig · kräftig|Stavros Ouzo ist eine Spirituose nach griechischer Art. Sein ausgeprägtes Anisaroma sorgt für den typischen mediterranen Charakter.
101|Himbeergeist|Himbeere · fruchtig · klar|Mathis Bür Himbeergeist bringt das charakteristische Aroma von Himbeeren zur Geltung. Eine klare Obstspirituose mit fruchtigem Duft und trockenem Eindruck.
102|Kirschwasser Schwarzwälder|Kirsche · fruchtig · kräftig|Schwarzwälder Kirschwasser ist ein klassischer Obstbrand aus Kirschen. Es verbindet ein klares Fruchtaroma mit dem kräftigen Charakter eines Destillats.
103|Obstler|Obst · fruchtig · trocken|Brandstädter Obstler ist ein klassischer Obstbrand. Seine fruchtige Aromatik steht im Mittelpunkt und klingt typisch trocken aus.
104|Williams|Birne · fruchtig · klar|Schwarzwaldhof Williams ist ein Birnenbrand mit dem charakteristischen Aroma der Williamsbirne. Eine klare, fruchtbetonte Spirituose für Liebhaber von Obstbränden.
105|Doppelkorn|Korn · klar · mild|Brandstädter Doppelkorn ist eine traditionelle deutsche Getreidespirituose. Sein klarer, geradliniger Geschmack macht ihn zum klassischen Schnaps.
106|Marillen select|Marille · fruchtig · aromatisch|Marillen Select ist eine Spirituosenspezialität mit Aprikosencharakter. Fruchtige Marillennoten stehen im Vordergrund; die genaue Produktvariante ist noch zu bestätigen.
107|Grappa Destillato|Traube · trocken · klar|Cellini Grappa Destillato ist ein italienischer Tresterbrand. Sein traubiger, klarer Charakter macht ihn zu einem klassischen Digestif.
108|Grappa Invecchiata|Trester · Holz · gereift|Cellini Grappa Invecchiata ist eine gereifte Variante des italienischen Tresterbrands. Die Reifung verleiht dem typischen Grappa-Charakter eine wärmere Note.
109|Tequila Silver|Agave · klar · würzig|Sierra Tequila Silver ist ein klarer Tequila mit charakteristischem Agavenprofil. Er zeigt einen direkten, würzigen Geschmack und eignet sich auch zum Mixen.
110|Tequila Reposado|Agave · Holz · mild würzig|Sierra Tequila Reposado ist ein Tequila mit Fassreifung. Typischer Agavencharakter verbindet sich mit milderen Holznoten.
111|Absinth 66 ★|Anis · Kräuter · intensiv|Absinth 66 ist eine kräftige Spirituose mit ausgeprägtem Kräutercharakter. Anisartige Noten prägen den intensiven Geschmack.
112|Amaretto|Mandel · süß · weich|Rialto Amaretto ist ein süßer Likör mit typischem Mandelaroma. Seine weiche Art passt sowohl zum puren Genuss als auch zu Mixgetränken.
113|Viagra Schnaps Spezial|Haus-Spezialität · Rezept offen|Viagra Schnaps Spezial ist eine Haus-Spezialität der Bierakademie. Zusammensetzung und Geschmacksrichtung sind noch nicht dokumentiert und sollten beim Betreiber erfragt werden.
114|Gletscherwasser|Kräuterig · frisch · würzig|Steinhauser Gletscherwasser ist eine Spirituosenspezialität mit erfrischendem Charakter. Das genaue Aromaprofil sollte anhand der verwendeten Variante bestätigt werden.
115|Banane|Banane · süß · tropisch|Bols Banane ist ein fruchtiger Likör mit ausgeprägtem Bananenaroma. Seine tropische Süße eignet sich besonders gut für Cocktails.
116|Batida de Coco|Kokos · cremig · süß|Mangaroca Batida de Coco ist ein cremiger Kokoslikör. Die milde, tropische Süße macht ihn zu einer beliebten Cocktailzutat.
117|Coconut|Kokos · süß · weich|Malibu Coconut verbindet die Süße von Kokos mit einem leichten Rumcharakter. Ein tropischer Likör für fruchtige Mixgetränke oder den puren Genuss.
118|Irish Cream|Sahne · Kakao · weich|Baileys Irish Cream ist ein cremiger Likör mit irischem Whiskeycharakter. Sanfte Sahne- und Kakaonoten sorgen für einen süßen, weichen Geschmack.
119|Goldwasser|Süß · würzig · goldene Flocken|Goldwasser ist eine traditionelle Likörspezialität mit charakteristischen Goldflocken. Je nach Hersteller können Würze und Süße unterschiedlich ausfallen.
120|Edelkirsch|Kirsche · fruchtig · süß|Eckes Edelkirsch ist ein Kirschlikör mit fruchtbetontem Charakter. Eine angenehme Süße begleitet das kräftige Kirscharoma.
121|Coffee Liqueur|Kaffee · süß · vollmundig|Kahlúa ist ein Kaffeelikör mit intensivem Kaffeearoma. Seine ausgeprägte Süße macht ihn zur beliebten Zutat für Desserts und Cocktails.
122|Sambuca|Anis · süß · intensiv|Graziani Sambuca ist ein italienisch geprägter Anislikör. Das intensive Anisaroma verbindet sich mit deutlicher Süße.
123|Pfefferminz|Minze · kühl · süß|Dieser Pfefferminzlikör setzt auf ein frisches Minzaroma. Die süße, kühlende Geschmacksrichtung macht ihn zu einem klassischen Kräuterlikör.
124|Bärwurz|Wurzelwürzig · herb · kräftig|Penninger Bärwurz ist eine bayerische Kräuter- und Wurzelspezialität. Sein markant würziger Geschmack richtet sich an Liebhaber kräftiger Schnäpse.
125|Kräuterlikör|Kräuter · würzig · bittersüß|Jägermeister ist ein Kräuterlikör mit komplexer Würze. Herbale Noten und eine bittersüße Aromatik sorgen für seinen charakteristischen Geschmack.
126|Kräuterbitter|Kräuter · bitter · intensiv|Underberg ist ein Kräuterbitter mit intensivem Geschmack. Ausgeprägte Kräuterwürze und ein herber Abgang stehen im Vordergrund.
127|Amaro|Kräuter · bittersüß · Zitrus|Ramazzotti Amaro ist ein italienischer Kräuterlikör mit bittersüßem Charakter. Kräuter- und Zitrusnoten machen ihn zu einem klassischen Aperitif oder Digestif.
128|Amaro|Kräuter · vollmundig · bittersüß|Averna Amaro ist eine italienische Kräuterlikör-Spezialität. Seine vollmundige, bittersüße Aromatik verbindet dunkle Kräuternoten mit sanfter Süße.
129|Bianco|Süßlich · Kräuter · Vanille|Martini Bianco ist ein aromatisierter Wein-Aperitif. Seine milde Süße trifft auf Kräuter- und Vanilleanklänge.
130|Tocco Rosso|Aperitif · bitter · Variante offen|Unter der Bezeichnung Campari Tocco Rosso wird in der gedruckten Karte ein Aperitif geführt. Die genaue Rezeptur dieser Position muss vor einer konkreten Geschmacksbeschreibung bestätigt werden.
131|Original|Orange · bittersüß · frisch|Aperol ist ein italienischer Aperitif mit charakteristischer Orangennote. Seine bittersüße Frische eignet sich besonders für Spritz-Getränke.
132|Schwäbischer Landwein|Trocken · fruchtig · harmonisch|Der Schwäbische Landwein von Schloss Affaltrach stammt aus Obersulm. Seine trockene Art bietet einen unkomplizierten Weingenuss aus der Region.
133|Gr. Merlot Rotwein Agioritiko|Trocken · rotfruchtig · kräftig|Dieser griechische Rotwein wird auf der Getränkekarte als trockener Merlot beziehungsweise Agioritiko geführt. Er steht für einen eher kräftigen Rotweinstil; die genaue Rebsortenangabe sollte noch geklärt werden.
134|Rotwein|Lieblich · weich · vollmundig|Apelia Rotwein aus Griechenland zeigt einen lieblichen, vollmundigen Charakter. Seine sanfte Süße macht ihn zu einer zugänglichen Alternative zu trockenen Rotweinen.
135|Mavrodaphne Likörwein|Lieblich · würzig · vollmundig|Mavrodaphne ist ein griechischer Likörwein mit lieblichem Charakter. Laut Getränkekarte zeichnet ihn eine besondere lorbeerartige Würze aus.
136|Rosé-Schillerwein|Trocken · frisch · rosé|Der Rosé-Schillerwein von Schloss Affaltrach stammt aus Obersulm. Ein trockener, frischer Wein für alle, die eine leichte Rosé-Stilrichtung bevorzugen.
137|Riesling Weißwein|Trocken · frisch · feinfruchtig|Dieser Riesling aus der Region Heilbronn-Staufenberg wird trocken angeboten. Eine frische, feinfruchtige Weißweinwahl für gemütliche Abende.
138|Retsina|Harzig · würzig · trocken|Malamatina Retsina ist eine traditionelle griechische Weißweinspezialität. Das charakteristische Harzaroma verleiht ihm einen unverwechselbar würzigen Geschmack.
139|Weinschorle Weiß / Rot / Rosé|Spritzig · frisch · Weiß/Rot/Rosé|Bei der Weinschorle wird Wein mit Sprudelwasser gemischt. Zur Wahl stehen Weißwein, Rotwein oder Rosé – jeweils mit eigenem Fruchtcharakter.
140|Mavrodaphne Schorle|Lieblich · fruchtig · spritzig|Diese Schorle verbindet den lieblichen griechischen Mavrodaphne mit prickelndem Wasser. So trifft der würzige Likörweincharakter auf erfrischende Leichtigkeit.
141|Aperol Spritz mit Sekt Yescovino|Orange · bittersüß · prickelnd|Dieser Aperol Spritz wird laut Karte mit Sekt von Yescovino gemixt. Bitterorange und lebendige Kohlensäure ergeben einen erfrischenden Aperitif.
142|Hugo|Holunder · Minze · Limette|Hugo ist ein erfrischender Aperitif mit typischen Holunder-, Minz- und Limettennoten. Die prickelnde Mischung verbindet fruchtige Süße mit frischer Kräuteraromatik.
143|Korea|Hauscocktail · Rezept offen|Korea wird in der Getränkekarte als Hausgetränk geführt. Die Zutaten und der genaue Geschmack sind noch nicht dokumentiert und müssen mit dem Betreiber geklärt werden.
144|Glühwein|Warm · würzig · fruchtig|Der hausgemachte Glühwein wird laut Getränkekarte aus Wein zubereitet und das ganze Jahr angeboten. Warm serviert steht sein fruchtiger, würziger Charakter im Mittelpunkt.
145|Sekt|Halbtrocken · perlend · mild|Yescovino Sekt wird in der Getränkekarte als halbtrocken geführt. Seine lebendige Perlage verbindet sich mit einer angenehmen, dezenten Süße.
146|Sektschorle Yescovino|Prickelnd · mild · erfrischend|Für diese Sektschorle wird Yescovino Sekt mit spritzigem Wasser kombiniert. Eine leichte, erfrischende Alternative zum puren Sekt.
147|Prosecco|Halbtrocken · fruchtig · prickelnd|Der Yescovino Prosecco wird laut Getränkekarte halbtrocken angeboten. Eine lebendige Perlage und sanfte Fruchtnoten prägen den italienischen Schaumweingenuss.
148|Proseccoschorle|Fruchtig · perlend · leicht|Bei der Proseccoschorle trifft Prosecco auf spritziges Wasser. Das Ergebnis ist ein leichter Aperitif mit fruchtigem und prickelndem Charakter.
149|Sekt|Feinperlig · elegant · frisch|Fürst Metternich Sekt steht für einen klassischen Sektempfang. Eine feine Perlage sorgt für einen eleganten, frischen Eindruck; die konkrete Geschmacksstufe richtet sich nach der angebotenen Sorte.
150|Champagner Brut|Trocken · feinperlig · frisch|Etienne Dumont Champagner Brut ist ein trockener französischer Schaumwein. Seine feine Perlage macht ihn zu einer festlichen Wahl.
151|Merlot Rotwein (vegan, alkoholfrei)|Rotfruchtig · weich · alkoholfrei|Carl Jung Merlot ist eine alkoholfreie Rotweinalternative, die laut Karte vegan ist. Sein weicher, rotfruchtiger Charakter bietet Weingenuss ohne die übliche Alkoholstärke.
152|Schorle Merlot Carl Jung|Rotfruchtig · spritzig · alkoholfrei|Für diese Schorle wird der alkoholfreie Merlot von Carl Jung mit Sprudelwasser gemischt. So wird der Rotweincharakter erfrischend und leichter.
153|Sekt Sparkling Rosé (alkoholfrei)|Rosé · fruchtig · alkoholfrei|Sparkling Rosé ist eine alkoholfreie Alternative zu Rosé-Sekt. Seine rosétypische Fruchtigkeit trifft auf lebendige Kohlensäure.
154|Sekt Schorle Sparkling Rosé|Rosé · spritzig · alkoholfrei|Die alkoholfreie Rosé-Sektschorle verbindet Sparkling Rosé mit Mineralwasser. Fruchtiger Rosé-Charakter und prickelnde Frische stehen im Mittelpunkt.
155|Original|Cola · süß · prickelnd|Coca-Cola Original ist der bekannte Erfrischungsgetränk-Klassiker. Sein süßer, würziger Colageschmack wird von spritziger Kohlensäure begleitet.
156|Fanta|Orange · fruchtig · prickelnd|Fanta ist eine spritzige Orangenlimonade mit fruchtigem Geschmack. Eine süße, erfrischende Alternative zu Cola.
157|Zero|Cola · prickelnd · ohne Zucker|Coca-Cola Zero bietet den typischen Colageschmack ohne Zucker. Eine spritzige Erfrischung mit würziger Colanote.
158|Spezi|Cola · Orange · spritzig|Spezi kombiniert Cola und Orangenlimonade zu einem beliebten Mischgetränk. Fruchtige Orangennoten treffen auf die Würze von Cola.
159|Energy Drink|Süß · spritzig · Energy|effect Energy Drink ist ein kohlensäurehaltiges Erfrischungsgetränk mit typischem Energy-Drink-Geschmack. Süße und markante Säure ergeben einen lebendigen Eindruck.
160|Bitter Lemon|Bitter · Zitrone · prickelnd|Schweppes Bitter Lemon verbindet Zitronenfrische mit einer angenehm herben Note. Die feine Kohlensäure macht es zum Klassiker pur oder als Mixer.
161|Tonic Water|Herb · tonisch · spritzig|Schweppes Tonic Water ist ein prickelndes Bittergetränk. Seine typische herbe Tonic-Note passt pur ebenso wie in Mixgetränke.
162|Zitronenlimonade|Zitrone · süß-säuerlich · prickelnd|Die Zitronenlimonade von Silber Brunnen ist eine spritzige Erfrischung. Süße und Zitronensäure sorgen für einen lebendigen Geschmack.
163|Sprudelwasser filtriert|Neutral · kühl · spritzig|Filtriertes Wasser aus der Bierakademie mit erfrischender Kohlensäure. Pur, klar und die passende Begleitung zu jedem Gericht.
164|Stilles Wasser filtriert|Neutral · weich · still|Filtriertes Wasser aus der Bierakademie ohne Kohlensäure. Eine klare, stille Erfrischung für alle, die Wasser ohne Sprudel bevorzugen.
165|Orangensaft|Orange · fruchtig · süß-säuerlich|Dieser Orangensaft bietet den vollen, fruchtigen Geschmack der Orange. Laut Getränkekarte besteht er aus 100 Prozent Frucht.
166|Apfelsaft|Apfel · fruchtig · mild|Apfelsaft mit dem vertrauten Geschmack reifer Äpfel. Laut Getränkekarte handelt es sich um Saft aus 100 Prozent Frucht.
167|Johannisbeer-Nektar|Johannisbeere · herbfruchtig · säuerlich|Johannisbeer-Nektar verbindet das kräftige Beerenaroma mit einer angenehm säuerlichen Note. Laut Getränkekarte beträgt der Fruchtgehalt 33 Prozent.
168|Kirsch-Nektar|Kirsche · vollfruchtig · süß-säuerlich|Kumpf Kirsch-Nektar bietet einen kräftigen, fruchtigen Kirschgeschmack. Die Getränkekarte nennt einen Fruchtgehalt von 50 Prozent.
169|Alle Saftschorlen|Fruchtig · spritzig · nach Wahl|Unsere Saftschorlen kombinieren den gewählten Fruchtsaft oder Nektar mit Sprudelwasser. Zur Auswahl stehen Orange, Apfel, Johannisbeere und Kirsche.
170|Aperol (alkoholfrei)|Bitterorange · süßlich · alkoholfrei|Diese alkoholfreie Aperitif-Variante wird in der Karte unter Monin geführt. Sie orientiert sich geschmacklich an einem bittersüßen Orangenaperitif; die genaue Produktbezeichnung ist noch zu prüfen.
171|Cranberry|Cranberry · herb · säuerlich|Rabenhorst Cranberry steht für einen intensiv fruchtigen, herb-säuerlichen Beerengeschmack. Laut Getränkekarte beträgt der Fruchtgehalt 100 Prozent.
172|Cranberry|Cranberry · fruchtig · süß-säuerlich|Bols Cranberry bringt den typischen Geschmack der Cranberry ins Glas. Seine fruchtige, süß-säuerliche Aromatik eignet sich für alkoholfreie Mixgetränke.
173|Sangrita Ricante|Pikant · würzig · Rezept prüfen|Sangrita Ricante wird als alkoholfreie Getränkespezialität angeboten. Die genaue Zutatenliste und der Schärfegrad dieser Variante müssen noch beim Betreiber geprüft werden.
174|Campari-Cocktail (alkoholfrei)|Bittersüß · prickelnd · alkoholfrei|Dieser alkoholfreie Cocktail orientiert sich an einem klassischen Bitter-Aperitif. Nach Wahl wird er mit Soda, Tonic Water, Bitter Lemon oder Fanta serviert.
175|Aperol Spritz (alkoholfrei)|Orange · spritzig · alkoholfrei|Dieser alkoholfreie Aperol-Spritz-Stil kombiniert laut Karte Monin mit Sparkling Rosé und Sprudelwasser. Fruchtige Orange und prickelnde Frische bestimmen den Charakter.
176|Cranberry-Cocktail|Cranberry · Kirsche · spritzig|Für den Cranberry-Cocktail wird Bols Cranberry mit Kirschnektar und Sprudel gemischt. Herbfruchtige Beeren- und süßliche Kirschnoten ergeben eine lebendige Mischung.
177|Amaretto-Cocktail (alkoholfrei)|Mandel · Apfel · spritzig|Der alkoholfreie Amaretto-Cocktail kombiniert Benvenuti mit Apfelsaft und Sprudel. Süßliche Mandelnoten treffen auf fruchtige Apfelfrische.
178|Grenadine Granatapfel|Granatapfel · Orange · spritzig|Dieser alkoholfreie Grenadine-Cocktail wird laut Karte mit Orangensaft und Soda gemischt. Granatapfelartige Süße und fruchtige Orange ergeben einen erfrischenden Drink.
179|Sunshine Tee|Sommerfrüchte · duftig · mild|Sunshine Tee vom Teehaus Weirich ist eine lose Teemischung mit verschiedenen Sommerfrüchten. Sein fruchtiges Aroma sorgt für eine warme, gemütliche Teepause.
180|Kamillentee|Kamille · mild · blumig|Ein milder Kamillentee im Teebeutel mit zart blumigem Charakter. Warm serviert ist er eine sanfte Wahl für ruhige Momente.
181|Pfefferminztee|Minze · frisch · aromatisch|Pfefferminztee im Teebeutel mit klarem, frischem Minzaroma. Sein belebend wirkender Duft macht ihn zu einer beliebten Kräuterteewahl.
182|Grüner Tee|Grüntee · feinherb · frisch|Grüner Tee im Teebeutel mit feinem, leicht herbem Geschmack. Eine unkomplizierte Teewahl für alle, die ein weniger süßes Aroma bevorzugen.
183|Hagebuttentee|Hagebutte · fruchtig · säuerlich|Hagebuttentee aus dem Teebeutel bietet einen fruchtigen, leicht säuerlichen Geschmack. Seine angenehme Frische macht ihn zu einer klassischen Früchteteevariante.
184|Schwarztee|Kräftig · herb · aromatisch|Schwarztee im Teebeutel mit einem kräftigen, charakteristischen Teegeschmack. Pur oder nach Wunsch verfeinert ist er ein zeitloser Klassiker.
185|Früchtetee|Fruchtig · süß-säuerlich · duftig|Früchtetee im Teebeutel verbindet verschiedene fruchtige Aromen. Heiß aufgegossen entsteht eine angenehm duftende Alternative zu klassischem Schwarztee.
186|Minze-Ingwer Tee|Minze · Ingwer · würzig|Dieser Tee kombiniert die Frische von Minze mit der würzigen Note von Ingwer. Eine aromatische Mischung für alle, die Kräutertees mit etwas Schärfe mögen.
187|Tasse Kaffee|Kaffee · aromatisch · kräftig|Eine frisch servierte Tasse Kaffee mit klassischem Kaffeearoma. Der vertraute Geschmack lädt zu einer gemütlichen Pause ein.
188|Espresso|Intensiv · kräftig · Espresso|Ein kleiner, konzentrierter Espresso mit kräftigem Kaffeegeschmack. Ideal für alle, die ihr Kaffeearoma besonders intensiv mögen.
189|Wurstsalat|Herzhaft · würzig · frisch|Unser Wurstsalat kombiniert Lyoner und Emmentaler mit Zwiebeln, Radieschen, Paprika, Sellerie, Petersilie und Bauerngurken. Dazu werden zwei Brotscheiben serviert.
190|Landjäger Delikatesse|Rauchig · herzhaft · würzig|Zwei Landjäger mit kräftig geräuchertem, herzhaftem Charakter. Serviert mit zwei Brotscheiben als rustikale Brotzeit.
191|Großer Veganer Teller|Vegan · abwechslungsreich · Tagesangebot|Der große vegane Teller wird nach dem aktuellen Tagesangebot zusammengestellt. Welche pflanzlichen Spezialitäten enthalten sind, erfährst du beim Service.
192|Veganer Teller|Vegan · frisch · Tagesangebot|Ein veganer Teller mit wechselnder Zusammenstellung nach Tagesangebot. Die Zutaten richten sich nach der aktuellen Küche und können variieren.
193|Großer Vegetarischer Teller|Vegetarisch · vielfältig · Tagesangebot|Der große vegetarische Teller bietet eine wechselnde Auswahl nach Tagesangebot. Frag unser Team nach den aktuell verwendeten Zutaten und Beilagen.
194|Vegetarischer Teller|Vegetarisch · frisch · Tagesangebot|Ein vegetarischer Teller mit wechselnden Komponenten aus dem Tagesangebot. Die genaue Zusammenstellung kann täglich variieren.
195|Mezze Großer Spezialteller|Herzhaft · mediterran · vielfältig|Unser großer Mezze-Spezialteller vereint sechs Fleischbällchen, geräucherte Gigantenbohnen, Kartoffelsalat, Pikantiki und frischen Salat. Dazu servieren wir Tzatziki und Brot für eine abwechslungsreiche mediterrane Brotzeit.
""".strip()

# Einige Eintraege enthalten ungepruefte Produktvarianten oder Hausrezepte.
REVIEW_IDS = {12, 58, 59, 73, 79, 86, 87, 94, 95, 97, 98, 99, 106, 111, 113, 114, 119, 121, 130, 133, 135, 143, 149, 153, 170, 173}


def parse_data():
    entries = {}
    for line_number, line in enumerate(DATA.splitlines(), start=1):
        parts = line.split('|', 3)
        if len(parts) != 4:
            raise ValueError(f'Ungueltige Datenzeile {line_number}')
        raw_pk, name, taste, description = (part.strip() for part in parts)
        pk = int(raw_pk)
        if pk in entries:
            raise ValueError(f'Doppelte Position: {pk}')
        if not name or not taste or not description or len(taste) > 160:
            raise ValueError(f'Leere/zu lange Beschreibung: {pk}')
        entries[pk] = {
            'name': name,
            'geschmack_kurz': taste,
            'beschreibung': description,
        }

    if len(entries) != 195 or set(entries) != set(range(1, 196)):
        raise ValueError('Nicht exakt 195 Menu-Eintraege (PK 1 bis 195).')
    return entries


def main():
    parser = argparse.ArgumentParser(description='Importiert eigene Texte fuer 195 Menu-Positionen')
    parser.add_argument('--apply', action='store_true', help='Aenderungen wirklich in der Datenbank speichern')
    parser.add_argument('--overwrite', action='store_true', help='Auch bereits ausgefuellte Textfelder ersetzen')
    args = parser.parse_args()

    if args.overwrite and not args.apply:
        parser.error('--overwrite nur zusammen mit --apply verwenden')
    if not (BASE_DIR / 'manage.py').is_file():
        parser.error('Die Datei muss im Django-Projektordner neben manage.py liegen.')

    entries = parse_data()
    import django
    django.setup()
    from django.db import transaction
    from website.models import MenuItem

    fieldnames = {f.name for f in MenuItem._meta.fields}
    needed = {'geschmack_kurz', 'beschreibung'}
    if not needed.issubset(fieldnames):
        raise RuntimeError('Erst neue Felder in models.py aufnehmen und makemigrations/migrate ausfuehren.')

    with transaction.atomic():
        queryset = MenuItem.objects.select_for_update().filter(pk__in=entries)
        items = {obj.pk: obj for obj in queryset}
        missing = sorted(entries.keys() - items.keys())
        if missing:
            raise RuntimeError(f'Keine Positionen in Datenbank fuer PK: {missing}. Import abgebrochen.')

        mismatches = [
            (pk, entries[pk]['name'], items[pk].name)
            for pk in sorted(entries)
            if entries[pk]['name'] != items[pk].name
        ]
        if mismatches:
            for pk, expected, actual in mismatches[:20]:
                print(f'NICHT GLEICH PK {pk}: Datei={expected!r}, Datenbank={actual!r}')
            raise RuntimeError('Namen passen nicht zur JSON-Vorlage: keine Aenderungen vorgenommen.')

        to_update = []
        old_values = []
        field_changes = 0
        skipped = 0
        for pk in sorted(entries):
            obj = items[pk]
            data = entries[pk]
            old_values.append({
                'pk': pk,
                'name': obj.name,
                'geschmack_kurz': obj.geschmack_kurz,
                'beschreibung': obj.beschreibung,
            })
            changed = False
            for field in ('geschmack_kurz', 'beschreibung'):
                old = getattr(obj, field)
                new = data[field]
                if old == new:
                    continue
                if old and not args.overwrite:
                    continue
                if args.apply:
                    setattr(obj, field, new)
                field_changes += 1
                changed = True
            if changed:
                to_update.append(obj)
            else:
                skipped += 1

        mode = 'SCHREIBMODUS' if args.apply else 'VORSCHAU - KEINE AENDERUNGEN'
        print(f'\n=== {mode} ===')
        print(f'Eintraege der Quelle: {len(entries)}')
        print(f'Zu aktualisierende Positionen: {len(to_update)}')
        print(f'Zu aktualisierende Textfelder: {field_changes}')
        print(f'Uebersprungene Positionen: {skipped}')
        print(f'Zur fachlichen Pruefung markiert: {len(REVIEW_IDS)}')
        for obj in to_update[:8]:
            print(f"  PK {obj.pk:3d}: {obj.name} -> {entries[obj.pk]['geschmack_kurz']}")
        if len(to_update) > 8:
            print(f'  ... und {len(to_update)-8} weitere Positionen')

        if not args.apply:
            print('\nZum Importieren ausfuehren: python import_bierakademie_texte.py --apply')
            return

        if not to_update:
            print('Es sind keine Aenderungen erforderlich.')
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = BASE_DIR / f'bierakademie_texte_backup_{timestamp}.json'
        with backup_path.open('x', encoding='utf-8') as f:
            json.dump(old_values, f, ensure_ascii=False, indent=2)

        MenuItem.objects.bulk_update(to_update, ['geschmack_kurz', 'beschreibung'], batch_size=100)
        print(f'\nERFOLG: {len(to_update)} Positionen wurden aktualisiert.')
        print(f'Sicherung alter Texte: {backup_path.name}')
        print('Preise, Produktbilder, Herstellertexte und Publikationsstatus NICHT veraendert.')
        print('Hinweis: Fachliche Pruefung noch offen bei PK:', ', '.join(map(str, sorted(REVIEW_IDS))))


if __name__ == '__main__':
    main()
