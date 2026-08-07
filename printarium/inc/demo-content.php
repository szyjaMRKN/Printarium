<?php
/**
 * Import przykładowej zawartości sklepu: kategorie, produkty, strony i menu.
 *
 * Wszystkie tworzone obiekty oznaczane są meta `_printarium_demo`,
 * dzięki czemu można je później usunąć jednym kliknięciem.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

const PRINTARIUM_DEMO_FLAG = '_printarium_demo';

/* =========================================================================
 * DEFINICJE DANYCH
 * ====================================================================== */

/**
 * Główne kategorie sklepu.
 *
 * @return array
 */
function printarium_demo_categories() {
	return array(
		'terraria'           => array(
			'name'        => 'Terraria',
			'description' => 'Terraria dla bezkręgowców i małych gadów – od kompaktowych modeli nano po wysokie konstrukcje nadrzewne. Konstrukcja z akrylu i elementów drukowanych 3D, wentylacja krzyżowa i wygodny dostęp serwisowy.',
		),
		'terraria-plus'      => array(
			'name'        => 'Terraria plus',
			'description' => 'Rozbudowane wersje terrariów wyposażone w systemy dodatkowe: nawadnianie, oświetlenie LED i kontrolę mikroklimatu. Rozwiązania dla wymagających gatunków i hodowli długoterminowej.',
		),
		'formikaria-i-areny' => array(
			'name'        => 'Formikaria i areny',
			'description' => 'Modułowe formikaria oraz areny wybiegowe dla kolonii mrówek. System modułów pozwala rozbudowywać gniazdo wraz ze wzrostem kolonii – bez przesiedlania.',
		),
		'zwierzeta'          => array(
			'name'        => 'Zwierzęta',
			'description' => 'Kolonie mrówek, królowe oraz inne bezkręgowce z własnej hodowli. Każde zwierzę wysyłamy w bezpiecznym opakowaniu transportowym, wyłącznie przy sprzyjających warunkach pogodowych.',
		),
		'akcesoria'          => array(
			'name'        => 'Akcesoria',
			'description' => 'Wyposażenie uzupełniające: poidełka, podłoża, moduły łączące, oświetlenie i narzędzia do obsługi hodowli.',
		),
	);
}

/**
 * Atrybuty globalne produktów.
 *
 * @return array
 */
function printarium_demo_attributes() {
	return array(
		'kolor'    => array( 'label' => 'Kolor', 'terms' => array( 'Czarny', 'Biały', 'Transparentny' ) ),
		'material' => array( 'label' => 'Materiał', 'terms' => array( 'PLA', 'PETG', 'Akryl', 'Szkło' ) ),
		'rozmiar'  => array( 'label' => 'Rozmiar', 'terms' => array( 'Nano', 'S', 'M', 'L', 'XL' ) ),
	);
}

/**
 * Przykładowe produkty.
 *
 * @return array
 */
function printarium_demo_products() {
	return array(
		/* ---------------- Terraria ---------------- */
		array(
			'name'       => 'Terrarium Nano 15×15×20',
			'category'   => 'terraria',
			'price'      => 189,
			'stock'      => 12,
			'short'      => 'Kompaktowe terrarium do obserwacji pojedynczych osobników – idealne na biurko.',
			'desc'       => "Najmniejszy model z serii. Sprawdza się przy hodowli młodych modliszek, pająków skakunów i innych drobnych bezkręgowców.\n\nKonstrukcja z akrylu 3 mm w ramie drukowanej 3D, front otwierany na zawiasach, wentylacja siatkowa w dwóch płaszczyznach.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'Nano' ),
		),
		array(
			'name'       => 'Terrarium Kubik 20×20×30',
			'category'   => 'terraria',
			'price'      => 299,
			'stock'      => 8,
			'short'      => 'Uniwersalne terrarium sześcienne z pełnym dostępem od frontu.',
			'desc'       => "Model bazowy serii Kubik. Proporcje dobrane pod gatunki naziemne i nadrzewne o niewielkich wymaganiach przestrzennych.\n\nW zestawie: korpus, ruchoma przednia szyba, zestaw montażowy oraz instrukcja aranżacji.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'S' ),
		),
		array(
			'name'       => 'Terrarium Tropic 30×30×45',
			'category'   => 'terraria',
			'price'      => 449,
			'sale'       => 399,
			'stock'      => 5,
			'short'      => 'Wysokie terrarium tropikalne z podwyższonym progiem na podłoże.',
			'desc'       => "Wysokość 45 cm pozwala zbudować pełną aranżację z warstwą drenażu, podłożem i roślinnością żywą.\n\nPodwyższony próg utrzymuje podłoże na miejscu podczas otwierania frontu.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'M' ),
		),
		array(
			'name'       => 'Terrarium Arboreal 40×40×60',
			'category'   => 'terraria',
			'price'      => 699,
			'stock'      => 3,
			'short'      => 'Konstrukcja nadrzewna dla gatunków wymagających wysokości.',
			'desc'       => "Największy model w serii podstawowej. Wzmocniona rama, podwójne prowadnice frontu i górna kratownica pod oświetlenie.\n\nRekomendowany dla większych modliszek i ptaszników nadrzewnych.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'L' ),
		),

		/* ---------------- Terraria plus ---------------- */
		array(
			'name'       => 'Terrarium Plus Bio 30×30×45',
			'category'   => 'terraria-plus',
			'price'      => 749,
			'stock'      => 4,
			'short'      => 'Terrarium z wbudowanym systemem nawadniania i drenażem.',
			'desc'       => "Wersja rozszerzona modelu Tropic. Zintegrowany zbiornik, dysze zraszające i ukryty przelew utrzymują stabilną wilgotność bez codziennej obsługi.\n\nSystem można sterować ręcznie lub podłączyć do zewnętrznego sterownika czasowego.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'M' ),
		),
		array(
			'name'       => 'Terrarium Plus Light 40×40×50',
			'category'   => 'terraria-plus',
			'price'      => 899,
			'stock'      => 3,
			'short'      => 'Zestaw z oświetleniem LED o pełnym spektrum i sterownikiem doby.',
			'desc'       => "Panel LED zintegrowany z pokrywą, płynne rozjaśnianie i wygaszanie symulujące świt i zmierzch.\n\nSpektrum dobrane pod rośliny żywe – nagietki, mchy i paprocie utrzymują kondycję przez cały rok.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'L' ),
		),
		array(
			'name'       => 'Terrarium Plus Duo – dwustanowiskowe',
			'category'   => 'terraria-plus',
			'price'      => 999,
			'stock'      => 2,
			'short'      => 'Dwie niezależne komory w jednej obudowie, ze wspólną podstawą.',
			'desc'       => "Rozwiązanie dla hodowców prowadzących równolegle dwa stanowiska. Komory rozdzielone szczelną przegrodą, każda z własną wentylacją i frontem.\n\nOszczędza miejsce na regale przy zachowaniu pełnej separacji zwierząt.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'L' ),
		),
		array(
			'name'       => 'Terrarium Plus Climate 45×45×60',
			'category'   => 'terraria-plus',
			'price'      => 1149,
			'sale'       => 1049,
			'stock'      => 2,
			'short'      => 'Najbardziej rozbudowany model – nawadnianie, LED i kontrola temperatury.',
			'desc'       => "Wersja flagowa. Łączy system nawadniania, oświetlenie o pełnym spektrum oraz matę grzewczą z termostatem.\n\nWszystkie przewody prowadzone są w kanałach obudowy, dzięki czemu wnętrze pozostaje czyste wizualnie.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'XL' ),
		),

		/* ---------------- Formikaria i areny ---------------- */
		array(
			'name'       => 'Formikarium gipsowe Nano',
			'category'   => 'formikaria-i-areny',
			'price'      => 99,
			'stock'      => 20,
			'short'      => 'Pierwsze gniazdo dla młodej kolonii – prosty start bez kompromisów.',
			'desc'       => "Wkład gipsowy utrzymuje wilgotność przez wiele dni, co ułatwia prowadzenie kolonii na wczesnym etapie.\n\nPrzezroczysta pokrywa umożliwia obserwację komór bez otwierania gniazda.",
			'attributes' => array( 'kolor' => 'Biały', 'material' => 'PLA', 'rozmiar' => 'Nano' ),
		),
		array(
			'name'       => 'Formikarium modułowe M',
			'category'   => 'formikaria-i-areny',
			'price'      => 279,
			'sale'       => 249,
			'stock'      => 15,
			'short'      => 'Sześć komór, system łączenia modułów, pełna kontrola wilgotności.',
			'desc'       => "Podstawowy moduł systemu Printarium. Sześć komór o zróżnicowanej głębokości pozwala kolonii samodzielnie wybrać strefę o odpowiedniej wilgotności.\n\nModuły łączy się złączami 12 mm – gniazdo rozbudowujesz bez przesiedlania kolonii.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'PETG', 'rozmiar' => 'M' ),
		),
		array(
			'name'       => 'Formikarium modułowe L',
			'category'   => 'formikaria-i-areny',
			'price'      => 349,
			'stock'      => 9,
			'short'      => 'Dziewięć komór dla rozwiniętej kolonii średniej wielkości.',
			'desc'       => "Wersja powiększona modułu M. Dodatkowy rząd komór i szerszy kanał nawilżający.\n\nPolecana dla kolonii liczących powyżej 300 robotnic.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'PETG', 'rozmiar' => 'L' ),
		),
		array(
			'name'       => 'Formikarium modułowe XL',
			'category'   => 'formikaria-i-areny',
			'price'      => 449,
			'stock'      => 6,
			'short'      => 'Dwanaście komór z podwójnym systemem nawilżania.',
			'desc'       => "Największy pojedynczy moduł w ofercie. Dwa niezależne zbiorniki pozwalają utrzymać gradient wilgotności wewnątrz jednego gniazda.\n\nPrzeznaczone dla dużych kolonii gatunków takich jak Messor czy Camponotus.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'PETG', 'rozmiar' => 'XL' ),
		),
		array(
			'name'       => 'Arena wybiegowa 20×20',
			'category'   => 'formikaria-i-areny',
			'price'      => 129,
			'stock'      => 18,
			'short'      => 'Podstawowa arena z zabezpieczeniem antyucieczkowym.',
			'desc'       => "Przestrzeń żerowania dla kolonii. Gładka krawędź wewnętrzna oraz rowek na talk skutecznie ograniczają ucieczki.\n\nDwa wyprowadzenia 12 mm umożliwiają podłączenie gniazda z dowolnej strony.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'S' ),
		),
		array(
			'name'       => 'Arena XL 30×20 z podłożem',
			'category'   => 'formikaria-i-areny',
			'price'      => 199,
			'stock'      => 11,
			'short'      => 'Większa arena w komplecie z podłożem piaskowo-glinianym.',
			'desc'       => "Wersja rozszerzona areny podstawowej. W zestawie 1 kg podłoża oraz element dekoracyjny w formie korzenia.\n\nCztery wyprowadzenia pozwalają budować rozbudowane układy wielomodułowe.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'Akryl', 'rozmiar' => 'L' ),
		),

		/* ---------------- Zwierzęta ---------------- */
		array(
			'name'       => 'Lasius niger – królowa z jajami',
			'category'   => 'zwierzeta',
			'price'      => 49,
			'stock'      => 25,
			'short'      => 'Gatunek startowy – odporny, łatwy w prowadzeniu, szybko rosnący.',
			'desc'       => "Najczęściej polecany gatunek dla początkujących. Królowa zakłada kolonię samodzielnie, bez konieczności dokarmiania na etapie zakładania gniazda.\n\nWysyłka w probówce startowej z zapasem wody.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Messor barbarus – kolonia startowa',
			'category'   => 'zwierzeta',
			'price'      => 89,
			'stock'      => 14,
			'short'      => 'Kolonia z królową i 10–20 robotnicami. Gatunek ziarnojedny.',
			'desc'       => "Mrówki żniwiarki gromadzące nasiona – jeden z najbardziej widowiskowych gatunków w obserwacji.\n\nWyraźny polimorfizm robotnic, kolonia szybko osiąga imponujące rozmiary.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Camponotus ligniperda – kolonia',
			'category'   => 'zwierzeta',
			'price'      => 149,
			'stock'      => 7,
			'short'      => 'Duże mrówki gmachówki – kolonia z królową i robotnicami.',
			'desc'       => "Jeden z największych krajowych gatunków. Robotnice osiągają do 18 mm długości.\n\nWymaga zimowania – szczegółową instrukcję dołączamy do przesyłki.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Modliszka Hierodula sp. – L3',
			'category'   => 'zwierzeta',
			'price'      => 39,
			'stock'      => 30,
			'short'      => 'Nimfa w trzecim stadium – gatunek łatwy w hodowli.',
			'desc'       => "Duży, spokojny gatunek modliszki dobrze znoszący warunki pokojowe.\n\nKarmienie: muszki owocowe na wczesnym etapie, później świerszcze i muchy.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Grammostola pulchra – L2',
			'category'   => 'zwierzeta',
			'price'      => 129,
			'stock'      => 5,
			'short'      => 'Ptasznik naziemny o spokojnym usposobieniu.',
			'desc'       => "Gatunek często polecany na start w hodowli ptaszników – powolny, mało płochliwy, o niskich wymaganiach.\n\nDorosłe osobniki osiągają głęboko czarne ubarwienie.",
			'attributes' => array(),
		),

		/* ---------------- Akcesoria ---------------- */
		array(
			'name'       => 'Poidełko dla mrówek – komplet 2 szt.',
			'category'   => 'akcesoria',
			'price'      => 24,
			'stock'      => 40,
			'short'      => 'Bezpieczne poidełka z wkładem chroniącym przed utonięciem.',
			'desc'       => "Komplet dwóch poidełek z wkładem gąbkowym. Uzupełnianie wody bez otwierania areny.\n\nPasują do wszystkich aren z serii Printarium.",
			'attributes' => array( 'kolor' => 'Transparentny', 'material' => 'PETG' ),
		),
		array(
			'name'       => 'Moduł łączący 12 mm – 4 szt.',
			'category'   => 'akcesoria',
			'price'      => 29,
			'stock'      => 35,
			'short'      => 'Złącza do łączenia gniazd, aren i modułów rozszerzających.',
			'desc'       => "Zestaw czterech złączy z uszczelkami. Umożliwiają rozbudowę układu w dowolnym kierunku.\n\nW komplecie zaślepki do nieużywanych wyprowadzeń.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'PETG' ),
		),
		array(
			'name'       => 'Podłoże piaskowo-gliniane 2 kg',
			'category'   => 'akcesoria',
			'price'      => 34,
			'stock'      => 22,
			'short'      => 'Naturalne podłoże do aren i terrariów – wysterylizowane.',
			'desc'       => "Mieszanka piasku i gliny w proporcji sprzyjającej kopaniu korytarzy.\n\nPodłoże jest wysterylizowane termicznie i gotowe do użycia.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Zestaw pęset laboratoryjnych',
			'category'   => 'akcesoria',
			'price'      => 39,
			'stock'      => 26,
			'short'      => 'Trzy pęsety ze stali nierdzewnej – proste, zagięte i szerokie.',
			'desc'       => "Podstawowe narzędzia do obsługi hodowli: podawanie pokarmu, przenoszenie elementów aranżacji, prace serwisowe.\n\nStal nierdzewna, długość 12–16 cm.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Zraszacz ciśnieniowy 500 ml',
			'category'   => 'akcesoria',
			'price'      => 59,
			'stock'      => 17,
			'short'      => 'Precyzyjne zraszanie terrarium bez zalewania podłoża.',
			'desc'       => "Zraszacz z pompką ciśnieniową i regulowaną dyszą. Umożliwia równomierne nawilżenie bez tworzenia kałuż.\n\nPojemność 500 ml wystarcza na kilkanaście zabiegów.",
			'attributes' => array(),
		),
		array(
			'name'       => 'Oświetlenie LED 20 cm',
			'category'   => 'akcesoria',
			'price'      => 79,
			'stock'      => 0,
			'short'      => 'Listwa LED o pełnym spektrum do terrariów z roślinnością żywą.',
			'desc'       => "Listwa 20 cm z zasilaczem. Spektrum dobrane pod rośliny terrariowe.\n\nMontaż na magnesach – bez wiercenia w obudowie.",
			'attributes' => array( 'kolor' => 'Czarny', 'material' => 'PETG' ),
		),
	);
}

/**
 * Przykładowe strony informacyjne.
 *
 * @return array
 */
function printarium_demo_pages() {
	return array(
		'strona-glowna' => array(
			'title'   => 'Strona główna',
			'content' => '',
		),
		'oferta'        => array(
			'title'   => 'Oferta',
			'content' => "<h2>Co znajdziesz w naszej ofercie</h2>\n<p>Tekst przykładowy – do uzupełnienia. Projektujemy i produkujemy sprzęt hodowlany dla pasjonatów bezkręgowców. Każdy produkt powstaje w oparciu o własne projekty, druk 3D oraz obróbkę akrylu.</p>\n\n[printarium_categories]\n\n<h2>Jak pracujemy</h2>\n<p>Tekst przykładowy. Zaczynamy od rozmowy o gatunku i warunkach, jakie chcesz zapewnić zwierzętom. Następnie przygotowujemy projekt, wizualizację i wycenę. Po akceptacji przechodzimy do produkcji.</p>\n<ol>\n<li>Konsultacja i dobór rozwiązania</li>\n<li>Projekt i wizualizacja</li>\n<li>Produkcja – druk 3D i obróbka akrylu</li>\n<li>Testy szczelności i wentylacji</li>\n<li>Pakowanie i wysyłka</li>\n</ol>\n\n<h2>Projekty na zamówienie</h2>\n<p>Tekst przykładowy. Realizujemy nietypowe konstrukcje – gniazda o niestandardowych wymiarach, zestawy wielomodułowe, elementy do istniejących terrariów. Opisz swój pomysł, a przygotujemy wycenę.</p>\n<p><a class=\"btn btn--primary\" href=\"/kontakt/\">Napisz do nas</a></p>",
		),
		'kontakt'       => array(
			'title'   => 'Kontakt',
			'content' => "<p>Tekst przykładowy. Masz pytanie o produkt albo pomysł na projekt na zamówienie? Napisz – zwykle odpowiadamy w ciągu jednego dnia roboczego.</p>\n\n[printarium_contact_form title=\"Projekt na zamówienie\"]\n\n<h2>Dane kontaktowe</h2>\n<p>E-mail: kontakt@printarium.pl<br>Telefon: +48 000 000 000<br>Godziny pracy: poniedziałek–piątek, 9:00–17:00</p>\n\n<h2>Najczęstsze pytania</h2>\n[printarium_faq]",
		),
		'o-nas'         => array(
			'title'   => 'O nas',
			'content' => "<h2>Kim jesteśmy</h2>\n<p>Tekst przykładowy – do uzupełnienia. Printarium powstało z pasji do obserwacji bezkręgowców i z potrzeby sprzętu, którego nie dało się kupić w gotowej formie.</p>\n\n<h2>Jak powstają nasze produkty</h2>\n<p>Tekst przykładowy. Każdy projekt zaczyna się od modelu 3D. Prototypy testujemy we własnej hodowli, zanim trafią do oferty.</p>\n\n<h2>Nasze zasady</h2>\n<ul>\n<li>Materiały bezpieczne dla zwierząt</li>\n<li>Konstrukcje, które da się rozbudować, a nie wymienić</li>\n<li>Produkcja w Polsce, krótkie terminy realizacji</li>\n<li>Wsparcie po zakupie – doradzamy także po sprzedaży</li>\n</ul>",
		),
		'faq'           => array(
			'title'   => 'FAQ',
			'content' => "<p>Tekst przykładowy. Zebraliśmy pytania, które powtarzają się najczęściej. Jeśli nie znajdziesz tu odpowiedzi – napisz do nas.</p>\n\n[printarium_faq single=\"false\"]",
		),
		'dostawa-i-platnosci' => array(
			'title'   => 'Dostawa i płatności',
			'content' => "<h2>Formy dostawy</h2>\n<p>Tekst przykładowy – do uzupełnienia po ustaleniu umów z przewoźnikami.</p>\n<ul>\n<li>Kurier – 15,00 zł</li>\n<li>Paczkomat – 12,00 zł</li>\n<li>Odbiór osobisty – 0,00 zł</li>\n</ul>\n\n<h2>Formy płatności</h2>\n<ul>\n<li>Przelew tradycyjny</li>\n<li>Szybkie płatności online</li>\n<li>Płatność przy odbiorze</li>\n</ul>\n\n<h2>Czas realizacji</h2>\n<p>Tekst przykładowy. Produkty dostępne w magazynie wysyłamy w ciągu 1–3 dni roboczych. Projekty na zamówienie realizujemy w 7–21 dni roboczych.</p>\n\n<h2>Wysyłka zwierząt</h2>\n<p>Tekst przykładowy. Zwierzęta wysyłamy wyłącznie przy sprzyjających warunkach pogodowych, w opakowaniach termoizolacyjnych.</p>",
		),
		'zwroty-i-reklamacje' => array(
			'title'   => 'Zwroty i reklamacje',
			'content' => "<h2>Prawo odstąpienia od umowy</h2>\n<p>Tekst przykładowy – do zastąpienia treścią przygotowaną prawnie. Konsument może odstąpić od umowy w terminie 14 dni bez podania przyczyny.</p>\n\n<h2>Wyłączenia</h2>\n<p>Tekst przykładowy. Prawo odstąpienia nie obejmuje produktów wykonanych na indywidualne zamówienie oraz żywych zwierząt.</p>\n\n<h2>Reklamacje</h2>\n<p>Tekst przykładowy. Reklamację można złożyć drogą mailową. Rozpatrujemy ją w ciągu 14 dni od otrzymania zgłoszenia.</p>",
		),
		'regulamin'     => array(
			'title'   => 'Regulamin',
			'content' => "<p><em>Tekst przykładowy. Ten dokument należy zastąpić regulaminem przygotowanym lub sprawdzonym przez prawnika – poniższa treść jest wyłącznie szkieletem.</em></p>\n\n<h2>§1. Postanowienia ogólne</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>§2. Składanie zamówień</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>§3. Płatności i dostawa</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>§4. Odstąpienie od umowy</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>§5. Reklamacje</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>§6. Postanowienia końcowe</h2>\n<p>Tekst przykładowy.</p>",
		),
		'polityka-prywatnosci' => array(
			'title'   => 'Polityka prywatności',
			'content' => "<p><em>Tekst przykładowy. Ten dokument należy zastąpić polityką prywatności dopasowaną do faktycznie przetwarzanych danych.</em></p>\n\n<h2>Administrator danych</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>Zakres i cel przetwarzania</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>Pliki cookies</h2>\n<p>Tekst przykładowy.</p>\n\n<h2>Twoje prawa</h2>\n<p>Tekst przykładowy.</p>",
		),
	);
}

/* =========================================================================
 * IMPORT
 * ====================================================================== */

/**
 * Uruchamia pełny import.
 *
 * @param array $steps Które kroki wykonać: categories, attributes, products, pages, menus, settings.
 * @return array Podsumowanie w formie listy komunikatów.
 */
function printarium_run_demo_import( $steps = array() ) {
	$all = array( 'categories', 'attributes', 'products', 'pages', 'menus', 'settings' );

	if ( empty( $steps ) ) {
		$steps = $all;
	}

	$log = array();

	if ( in_array( 'categories', $steps, true ) ) {
		$log[] = printarium_import_categories();
	}
	if ( in_array( 'attributes', $steps, true ) ) {
		$log[] = printarium_import_attributes();
	}
	if ( in_array( 'products', $steps, true ) ) {
		$log[] = printarium_import_products();
	}
	if ( in_array( 'pages', $steps, true ) ) {
		$log[] = printarium_import_pages();
	}
	if ( in_array( 'menus', $steps, true ) ) {
		$log[] = printarium_import_menus();
	}
	if ( in_array( 'settings', $steps, true ) ) {
		$log[] = printarium_import_settings();
	}

	return array_filter( $log );
}

/**
 * Tworzy kategorie produktów.
 *
 * @return string
 */
function printarium_import_categories() {
	if ( ! printarium_is_woocommerce_active() ) {
		return __( 'Pominięto kategorie – WooCommerce nie jest aktywne.', 'printarium' );
	}

	$created = 0;
	$order   = 0;

	foreach ( printarium_demo_categories() as $slug => $data ) {
		$order += 1;
		$term   = get_term_by( 'slug', $slug, 'product_cat' );

		if ( ! $term ) {
			$result = wp_insert_term(
				$data['name'],
				'product_cat',
				array(
					'slug'        => $slug,
					'description' => $data['description'],
				)
			);

			if ( is_wp_error( $result ) ) {
				continue;
			}

			$term_id = $result['term_id'];
			update_term_meta( $term_id, PRINTARIUM_DEMO_FLAG, 1 );
			$created++;
		} else {
			$term_id = $term->term_id;
			wp_update_term( $term_id, 'product_cat', array( 'description' => $data['description'] ) );
		}

		update_term_meta( $term_id, 'order', $order );

		// Miniatura kategorii.
		if ( ! get_term_meta( $term_id, 'thumbnail_id', true ) ) {
			$image_id = printarium_create_placeholder_image( $data['name'], 'kategoria-' . $slug );
			if ( $image_id ) {
				update_term_meta( $term_id, 'thumbnail_id', $image_id );
			}
		}
	}

	return sprintf(
		/* translators: %d: liczba utworzonych kategorii. */
		__( 'Kategorie: utworzono %d, pozostałe zaktualizowano.', 'printarium' ),
		$created
	);
}

/**
 * Tworzy globalne atrybuty produktów wraz z wartościami.
 *
 * @return string
 */
function printarium_import_attributes() {
	if ( ! printarium_is_woocommerce_active() || ! function_exists( 'wc_create_attribute' ) ) {
		return '';
	}

	$created = 0;

	foreach ( printarium_demo_attributes() as $slug => $data ) {
		$taxonomy = wc_attribute_taxonomy_name( $slug );

		if ( ! taxonomy_exists( $taxonomy ) ) {
			$attribute_id = wc_create_attribute(
				array(
					'name'         => $data['label'],
					'slug'         => $slug,
					'type'         => 'select',
					'order_by'     => 'menu_order',
					'has_archives' => false,
				)
			);

			if ( is_wp_error( $attribute_id ) ) {
				continue;
			}

			register_taxonomy(
				$taxonomy,
				'product',
				array( 'hierarchical' => false, 'show_ui' => false, 'query_var' => true, 'rewrite' => false )
			);

			$created++;
		}

		foreach ( $data['terms'] as $term_name ) {
			if ( ! term_exists( $term_name, $taxonomy ) ) {
				wp_insert_term( $term_name, $taxonomy );
			}
		}
	}

	delete_transient( 'wc_attribute_taxonomies' );

	return sprintf(
		/* translators: %d: liczba utworzonych atrybutów. */
		__( 'Atrybuty produktów: utworzono %d.', 'printarium' ),
		$created
	);
}

/**
 * Tworzy przykładowe produkty.
 *
 * @return string
 */
function printarium_import_products() {
	if ( ! printarium_is_woocommerce_active() ) {
		return __( 'Pominięto produkty – WooCommerce nie jest aktywne.', 'printarium' );
	}

	$created = 0;
	$skipped = 0;

	foreach ( printarium_demo_products() as $data ) {
		$slug = sanitize_title( $data['name'] );

		if ( get_page_by_path( $slug, OBJECT, 'product' ) ) {
			$skipped++;
			continue;
		}

		$product = new WC_Product_Simple();
		$product->set_name( $data['name'] );
		$product->set_slug( $slug );
		$product->set_status( 'publish' );
		$product->set_catalog_visibility( 'visible' );
		$product->set_description( wpautop( $data['desc'] ) );
		$product->set_short_description( $data['short'] );
		$product->set_regular_price( (string) $data['price'] );

		if ( ! empty( $data['sale'] ) ) {
			$product->set_sale_price( (string) $data['sale'] );
		}

		$product->set_manage_stock( true );
		$product->set_stock_quantity( (int) $data['stock'] );
		$product->set_stock_status( $data['stock'] > 0 ? 'instock' : 'outofstock' );
		$product->set_sku( 'PR-' . strtoupper( substr( md5( $slug ), 0, 6 ) ) );

		// Atrybuty.
		if ( ! empty( $data['attributes'] ) ) {
			$attributes = array();
			$position   = 0;

			foreach ( $data['attributes'] as $attr_slug => $value ) {
				$taxonomy = wc_attribute_taxonomy_name( $attr_slug );

				if ( ! taxonomy_exists( $taxonomy ) ) {
					continue;
				}

				$term = get_term_by( 'name', $value, $taxonomy );

				if ( ! $term ) {
					continue;
				}

				$attribute = new WC_Product_Attribute();
				$attribute->set_id( wc_attribute_taxonomy_id_by_name( $taxonomy ) );
				$attribute->set_name( $taxonomy );
				$attribute->set_options( array( $term->term_id ) );
				$attribute->set_position( $position++ );
				$attribute->set_visible( true );
				$attribute->set_variation( false );

				$attributes[] = $attribute;
			}

			if ( $attributes ) {
				$product->set_attributes( $attributes );
			}
		}

		$product_id = $product->save();

		if ( ! $product_id ) {
			continue;
		}

		// Kategoria.
		wp_set_object_terms( $product_id, array( $data['category'] ), 'product_cat' );

		// Zdjęcie zastępcze.
		$image_id = printarium_create_placeholder_image( $data['name'], $slug );
		if ( $image_id ) {
			set_post_thumbnail( $product_id, $image_id );
		}

		update_post_meta( $product_id, PRINTARIUM_DEMO_FLAG, 1 );
		$created++;
	}

	return sprintf(
		/* translators: 1: liczba utworzonych produktów, 2: liczba pominiętych. */
		__( 'Produkty: utworzono %1$d, pominięto %2$d (już istniały).', 'printarium' ),
		$created,
		$skipped
	);
}

/**
 * Tworzy strony informacyjne.
 *
 * @return string
 */
function printarium_import_pages() {
	$created = 0;

	foreach ( printarium_demo_pages() as $slug => $data ) {
		if ( get_page_by_path( $slug ) ) {
			continue;
		}

		$page_id = wp_insert_post(
			array(
				'post_title'   => $data['title'],
				'post_name'    => $slug,
				'post_content' => $data['content'],
				'post_status'  => 'publish',
				'post_type'    => 'page',
			)
		);

		if ( $page_id && ! is_wp_error( $page_id ) ) {
			update_post_meta( $page_id, PRINTARIUM_DEMO_FLAG, 1 );
			$created++;
		}
	}

	return sprintf(
		/* translators: %d: liczba utworzonych stron. */
		__( 'Strony: utworzono %d.', 'printarium' ),
		$created
	);
}

/**
 * Buduje menu: główne, stopki i prawne.
 *
 * @return string
 */
function printarium_import_menus() {
	$locations = get_theme_mod( 'nav_menu_locations', array() );
	$built     = array();

	/* --- Menu główne --- */
	$primary_items = array();

	foreach ( array_keys( printarium_demo_categories() ) as $slug ) {
		$term = get_term_by( 'slug', $slug, 'product_cat' );
		if ( $term ) {
			$primary_items[] = array( 'type' => 'taxonomy', 'object' => 'product_cat', 'id' => $term->term_id );
		}
	}

	foreach ( array( 'oferta', 'kontakt' ) as $page_slug ) {
		$page = get_page_by_path( $page_slug );
		if ( $page ) {
			$primary_items[] = array( 'type' => 'post_type', 'object' => 'page', 'id' => $page->ID );
		}
	}

	if ( printarium_build_menu( __( 'Menu główne Printarium', 'printarium' ), $primary_items, 'primary', $locations ) ) {
		$built[] = __( 'główne', 'printarium' );
	}

	/* --- Menu stopki --- */
	$footer_items = array();

	foreach ( array( 'o-nas', 'oferta', 'dostawa-i-platnosci', 'faq', 'zwroty-i-reklamacje' ) as $page_slug ) {
		$page = get_page_by_path( $page_slug );
		if ( $page ) {
			$footer_items[] = array( 'type' => 'post_type', 'object' => 'page', 'id' => $page->ID );
		}
	}

	if ( printarium_build_menu( __( 'Stopka Printarium', 'printarium' ), $footer_items, 'footer', $locations ) ) {
		$built[] = __( 'stopki', 'printarium' );
	}

	/* --- Menu prawne --- */
	$legal_items = array();

	foreach ( array( 'regulamin', 'polityka-prywatnosci' ) as $page_slug ) {
		$page = get_page_by_path( $page_slug );
		if ( $page ) {
			$legal_items[] = array( 'type' => 'post_type', 'object' => 'page', 'id' => $page->ID );
		}
	}

	if ( printarium_build_menu( __( 'Menu prawne Printarium', 'printarium' ), $legal_items, 'legal', $locations ) ) {
		$built[] = __( 'prawne', 'printarium' );
	}

	set_theme_mod( 'nav_menu_locations', $locations );

	if ( empty( $built ) ) {
		return __( 'Menu: nic nie utworzono (menu już istnieją).', 'printarium' );
	}

	return sprintf(
		/* translators: %s: lista nazw menu. */
		__( 'Menu: utworzono i przypisano – %s.', 'printarium' ),
		implode( ', ', $built )
	);
}

/**
 * Tworzy pojedyncze menu i przypisuje je do lokalizacji.
 *
 * @param string $name      Nazwa menu.
 * @param array  $items     Pozycje.
 * @param string $location  Lokalizacja motywu.
 * @param array  $locations Referencja do mapy lokalizacji.
 * @return bool Czy menu zostało utworzone.
 */
function printarium_build_menu( $name, $items, $location, &$locations ) {
	if ( empty( $items ) ) {
		return false;
	}

	$menu = wp_get_nav_menu_object( $name );

	if ( $menu ) {
		$locations[ $location ] = $menu->term_id;
		return false;
	}

	$menu_id = wp_create_nav_menu( $name );

	if ( is_wp_error( $menu_id ) ) {
		return false;
	}

	foreach ( $items as $item ) {
		wp_update_nav_menu_item(
			$menu_id,
			0,
			array(
				'menu-item-type'      => $item['type'],
				'menu-item-object'    => $item['object'],
				'menu-item-object-id' => $item['id'],
				'menu-item-status'    => 'publish',
			)
		);
	}

	$locations[ $location ] = $menu_id;

	return true;
}

/**
 * Ustawienia witryny: strona główna, waluta, kraj sklepu.
 *
 * @return string
 */
function printarium_import_settings() {
	$front = get_page_by_path( 'strona-glowna' );

	if ( $front ) {
		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', $front->ID );
	}

	if ( printarium_is_woocommerce_active() ) {
		update_option( 'woocommerce_currency', 'PLN' );
		update_option( 'woocommerce_currency_pos', 'right_space' );
		update_option( 'woocommerce_price_decimal_sep', ',' );
		update_option( 'woocommerce_price_thousand_sep', ' ' );
		update_option( 'woocommerce_default_country', 'PL' );
		update_option( 'woocommerce_weight_unit', 'kg' );
		update_option( 'woocommerce_dimension_unit', 'cm' );
		update_option( 'woocommerce_catalog_columns', 4 );
		update_option( 'woocommerce_catalog_rows', 3 );
	}

	// WordPress wypełnia pierwszy zarejestrowany obszar widgetów domyślnymi
	// widgetami („Archiwa”, „Kategorie”…). W stopce motywu wyglądają obco,
	// więc czyścimy obszary stopki – własne widgety użytkownika zostają.
	printarium_clear_default_widgets();

	// Ładne odnośniki – wymagane przez WooCommerce.
	if ( ! get_option( 'permalink_structure' ) ) {
		update_option( 'permalink_structure', '/%postname%/' );
		flush_rewrite_rules();
	}

	return __( 'Ustawienia: strona główna, waluta PLN i format cen zostały skonfigurowane.', 'printarium' );
}

/**
 * Usuwa domyślne widgety WordPressa z obszarów stopki i sidebara sklepu.
 *
 * Dotyczy wyłącznie widgetów wstawionych automatycznie przy instalacji
 * (archiwa, kategorie, ostatnie wpisy, komentarze, meta, wyszukiwarka).
 */
function printarium_clear_default_widgets() {
	$defaults = array( 'archives', 'categories', 'recent-posts', 'recent-comments', 'meta', 'search', 'block' );
	$sidebars = get_option( 'sidebars_widgets', array() );
	$areas    = array( 'footer-1', 'footer-2', 'footer-3', 'shop-sidebar' );
	$changed  = false;

	foreach ( $areas as $area ) {
		if ( empty( $sidebars[ $area ] ) || ! is_array( $sidebars[ $area ] ) ) {
			continue;
		}

		$kept = array();

		foreach ( $sidebars[ $area ] as $widget_id ) {
			$base = preg_replace( '/-\d+$/', '', $widget_id );

			if ( in_array( $base, $defaults, true ) ) {
				$changed = true;
				continue;
			}

			$kept[] = $widget_id;
		}

		$sidebars[ $area ] = $kept;
	}

	if ( $changed ) {
		update_option( 'sidebars_widgets', $sidebars );
	}
}

/* =========================================================================
 * ZDJĘCIA ZASTĘPCZE
 * ====================================================================== */

/**
 * Generuje proste zdjęcie zastępcze w stylistyce motywu i dodaje je do biblioteki.
 *
 * Wymaga rozszerzenia GD. Gdy jest niedostępne – zwraca 0.
 *
 * @param string $label Nazwa wyświetlana na obrazku.
 * @param string $slug  Slug pliku.
 * @return int ID załącznika lub 0.
 */
function printarium_create_placeholder_image( $label, $slug ) {
	if ( ! function_exists( 'imagecreatetruecolor' ) ) {
		return 0;
	}

	$existing = get_posts(
		array(
			'post_type'      => 'attachment',
			'name'           => 'printarium-' . $slug,
			'posts_per_page' => 1,
			'post_status'    => 'inherit',
			'fields'         => 'ids',
		)
	);

	if ( ! empty( $existing ) ) {
		return (int) $existing[0];
	}

	$size  = 1000;
	$image = imagecreatetruecolor( $size, $size );

	$bg     = imagecolorallocate( $image, 13, 25, 19 );   // #0D1913
	$deep   = imagecolorallocate( $image, 7, 17, 13 );    // #07110D
	$green  = imagecolorallocate( $image, 130, 155, 47 ); // #829B2F
	$text   = imagecolorallocate( $image, 243, 244, 239 );

	imagefill( $image, 0, 0, $bg );

	// Delikatna winieta – ciemniejsze narożniki.
	for ( $i = 0; $i < 60; $i++ ) {
		imagerectangle( $image, $i, $i, $size - $i - 1, $size - $i - 1, $i % 2 ? $deep : $bg );
	}

	// Heksagon w kolorze marki.
	$cx = $size / 2;
	$cy = $size / 2 - 30;
	$r  = 210;

	for ( $w = 0; $w < 5; $w++ ) {
		$points = array();
		for ( $a = 0; $a < 6; $a++ ) {
			$angle    = deg2rad( 60 * $a - 90 );
			$points[] = (int) round( $cx + ( $r - $w ) * cos( $angle ) );
			$points[] = (int) round( $cy + ( $r - $w ) * sin( $angle ) );
		}
		if ( function_exists( 'imagepolygon' ) ) {
			imagepolygon( $image, $points, $green );
		}
	}

	// Nazwa produktu na dole (bitmapowy font GD – wystarcza dla podglądu).
	$caption = mb_substr( wp_strip_all_tags( $label ), 0, 34 );
	$caption = function_exists( 'iconv' ) ? iconv( 'UTF-8', 'ASCII//TRANSLIT', $caption ) : $caption;
	$width   = imagefontwidth( 5 ) * strlen( (string) $caption );
	imagestring( $image, 5, (int) ( ( $size - $width ) / 2 ), $size - 140, (string) $caption, $text );
	imagestring( $image, 3, (int) ( ( $size - imagefontwidth( 3 ) * 9 ) / 2 ), $size - 110, 'PRINTARIUM', $green );

	$upload = wp_upload_dir();
	$file   = trailingslashit( $upload['path'] ) . 'printarium-' . $slug . '.jpg';

	imagejpeg( $image, $file, 86 );
	imagedestroy( $image );

	$attachment_id = wp_insert_attachment(
		array(
			'post_mime_type' => 'image/jpeg',
			'post_title'     => $label,
			'post_name'      => 'printarium-' . $slug,
			'post_status'    => 'inherit',
		),
		$file
	);

	if ( is_wp_error( $attachment_id ) || ! $attachment_id ) {
		return 0;
	}

	require_once ABSPATH . 'wp-admin/includes/image.php';
	wp_update_attachment_metadata( $attachment_id, wp_generate_attachment_metadata( $attachment_id, $file ) );
	update_post_meta( $attachment_id, PRINTARIUM_DEMO_FLAG, 1 );

	return (int) $attachment_id;
}

/* =========================================================================
 * USUWANIE DANYCH DEMO
 * ====================================================================== */

/**
 * Usuwa wszystkie obiekty oznaczone jako demo.
 *
 * @return string
 */
function printarium_remove_demo_content() {
	$deleted = 0;

	$posts = get_posts(
		array(
			'post_type'      => array( 'product', 'page', 'attachment' ),
			'post_status'    => 'any',
			'posts_per_page' => -1,
			'fields'         => 'ids',
			'meta_key'       => PRINTARIUM_DEMO_FLAG, // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_key
			'meta_value'     => 1, // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_value
		)
	);

	foreach ( $posts as $post_id ) {
		wp_delete_post( $post_id, true );
		$deleted++;
	}

	if ( taxonomy_exists( 'product_cat' ) ) {
		foreach ( array_keys( printarium_demo_categories() ) as $slug ) {
			$term = get_term_by( 'slug', $slug, 'product_cat' );
			if ( $term && get_term_meta( $term->term_id, PRINTARIUM_DEMO_FLAG, true ) ) {
				wp_delete_term( $term->term_id, 'product_cat' );
				$deleted++;
			}
		}
	}

	foreach ( array( __( 'Menu główne Printarium', 'printarium' ), __( 'Stopka Printarium', 'printarium' ), __( 'Menu prawne Printarium', 'printarium' ) ) as $menu_name ) {
		$menu = wp_get_nav_menu_object( $menu_name );
		if ( $menu ) {
			wp_delete_nav_menu( $menu->term_id );
			$deleted++;
		}
	}

	return sprintf(
		/* translators: %d: liczba usuniętych elementów. */
		__( 'Usunięto %d elementów danych demonstracyjnych.', 'printarium' ),
		$deleted
	);
}
