<?php
/**
 * Opcje motywu w Personalizatorze (Wygląd → Dostosuj).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Domyślne wartości opcji motywu.
 *
 * @return array
 */
function printarium_defaults() {
	return array(
		'printarium_google_fonts'    => true,
		'printarium_hero_title'      => __( 'Natura w <em>nowoczesnej</em> formie', 'printarium' ),
		'printarium_hero_text'       => __( 'Projektujemy formikaria i terraria, które łączą funkcjonalność, estetykę i technologię.', 'printarium' ),
		'printarium_hero_btn1_label' => __( 'Zobacz ofertę', 'printarium' ),
		'printarium_hero_btn1_url'   => '/sklep/',
		'printarium_hero_btn2_label' => __( 'Projekt na zamówienie', 'printarium' ),
		'printarium_hero_btn2_url'   => '/kontakt/',
		'printarium_hero_image'      => '',
		'printarium_usp_1'           => __( 'Projektowane w Polsce', 'printarium' ),
		'printarium_usp_2'           => __( 'Druk 3D i akryl', 'printarium' ),
		'printarium_usp_3'           => __( 'Personalizacja', 'printarium' ),
		'printarium_usp_4'           => __( 'Bezpieczne dla zwierząt', 'printarium' ),
		'printarium_products_title'  => __( 'Stworzone dla Twojego świata', 'printarium' ),
		'printarium_products_text'   => __( 'Modularne rozwiązania i unikalne projekty dopasowane do Ciebie i Twoich zwierząt.', 'printarium' ),
		'printarium_footer_about'    => __( 'Printarium projektuje i produkuje formikaria, terraria oraz akcesoria dla hodowców bezkręgowców. Druk 3D, akryl i dbałość o detale.', 'printarium' ),
		'printarium_contact_email'   => 'kontakt@printarium.pl',
		'printarium_contact_phone'   => '+48 000 000 000',
		'printarium_contact_address' => __( 'Polska', 'printarium' ),
		'printarium_copyright'       => '',
	);
}

/**
 * Pobiera wartość opcji motywu.
 *
 * @param string $key Klucz.
 * @return mixed
 */
function printarium_option( $key ) {
	$defaults = printarium_defaults();
	$default  = isset( $defaults[ $key ] ) ? $defaults[ $key ] : '';

	return get_theme_mod( $key, $default );
}

/**
 * Rejestracja sekcji i ustawień.
 *
 * @param WP_Customize_Manager $wp_customize Personalizator.
 */
function printarium_customize_register( $wp_customize ) {
	$defaults = printarium_defaults();

	$wp_customize->add_panel(
		'printarium_panel',
		array(
			'title'    => __( 'Printarium – ustawienia motywu', 'printarium' ),
			'priority' => 20,
		)
	);

	/* ---------- Sekcja: Ogólne ---------- */
	$wp_customize->add_section(
		'printarium_general',
		array(
			'title' => __( 'Ogólne', 'printarium' ),
			'panel' => 'printarium_panel',
		)
	);

	$wp_customize->add_setting(
		'printarium_google_fonts',
		array(
			'default'           => $defaults['printarium_google_fonts'],
			'sanitize_callback' => 'printarium_sanitize_checkbox',
		)
	);
	$wp_customize->add_control(
		'printarium_google_fonts',
		array(
			'label'       => __( 'Ładuj font Montserrat z Google Fonts', 'printarium' ),
			'description' => __( 'Wyłącz, jeśli hostujesz font lokalnie (np. ze względu na RODO).', 'printarium' ),
			'section'     => 'printarium_general',
			'type'        => 'checkbox',
		)
	);

	/* ---------- Sekcja: Hero ---------- */
	$wp_customize->add_section(
		'printarium_hero',
		array(
			'title'       => __( 'Strona główna – Hero', 'printarium' ),
			'panel'       => 'printarium_panel',
			'description' => __( 'Wyróżnij fragment tytułu znacznikiem &lt;em&gt;, aby podświetlić go na zielono.', 'printarium' ),
		)
	);

	$hero_fields = array(
		'printarium_hero_title'      => array( __( 'Tytuł', 'printarium' ), 'textarea' ),
		'printarium_hero_text'       => array( __( 'Opis', 'printarium' ), 'textarea' ),
		'printarium_hero_btn1_label' => array( __( 'Przycisk 1 – etykieta', 'printarium' ), 'text' ),
		'printarium_hero_btn1_url'   => array( __( 'Przycisk 1 – adres', 'printarium' ), 'url' ),
		'printarium_hero_btn2_label' => array( __( 'Przycisk 2 – etykieta', 'printarium' ), 'text' ),
		'printarium_hero_btn2_url'   => array( __( 'Przycisk 2 – adres', 'printarium' ), 'url' ),
	);

	foreach ( $hero_fields as $key => $field ) {
		$wp_customize->add_setting(
			$key,
			array(
				'default'           => $defaults[ $key ],
				'sanitize_callback' => 'url' === $field[1] ? 'esc_url_raw' : 'wp_kses_post',
				'transport'         => 'postMessage',
			)
		);
		$wp_customize->add_control(
			$key,
			array(
				'label'   => $field[0],
				'section' => 'printarium_hero',
				'type'    => $field[1],
			)
		);
	}

	$wp_customize->add_setting(
		'printarium_hero_image',
		array(
			'default'           => '',
			'sanitize_callback' => 'absint',
		)
	);
	$wp_customize->add_control(
		new WP_Customize_Media_Control(
			$wp_customize,
			'printarium_hero_image',
			array(
				'label'     => __( 'Zdjęcie / tło sekcji hero', 'printarium' ),
				'section'   => 'printarium_hero',
				'mime_type' => 'image',
			)
		)
	);

	/* ---------- Sekcja: Pasek atutów ---------- */
	$wp_customize->add_section(
		'printarium_usp',
		array(
			'title' => __( 'Strona główna – pasek atutów', 'printarium' ),
			'panel' => 'printarium_panel',
		)
	);

	for ( $i = 1; $i <= 4; $i++ ) {
		$key = 'printarium_usp_' . $i;
		$wp_customize->add_setting(
			$key,
			array(
				'default'           => $defaults[ $key ],
				'sanitize_callback' => 'sanitize_text_field',
				'transport'         => 'postMessage',
			)
		);
		$wp_customize->add_control(
			$key,
			array(
				/* translators: %d: numer atutu. */
				'label'   => sprintf( __( 'Atut %d', 'printarium' ), $i ),
				'section' => 'printarium_usp',
				'type'    => 'text',
			)
		);
	}

	/* ---------- Sekcja: Sekcja produktowa ---------- */
	$wp_customize->add_section(
		'printarium_products',
		array(
			'title' => __( 'Strona główna – sekcja produktów', 'printarium' ),
			'panel' => 'printarium_panel',
		)
	);

	foreach ( array( 'printarium_products_title' => __( 'Tytuł sekcji', 'printarium' ), 'printarium_products_text' => __( 'Podtytuł sekcji', 'printarium' ) ) as $key => $label ) {
		$wp_customize->add_setting(
			$key,
			array(
				'default'           => $defaults[ $key ],
				'sanitize_callback' => 'wp_kses_post',
				'transport'         => 'postMessage',
			)
		);
		$wp_customize->add_control(
			$key,
			array(
				'label'   => $label,
				'section' => 'printarium_products',
				'type'    => 'text',
			)
		);
	}

	/* ---------- Sekcja: Stopka i kontakt ---------- */
	$wp_customize->add_section(
		'printarium_footer',
		array(
			'title' => __( 'Stopka i dane kontaktowe', 'printarium' ),
			'panel' => 'printarium_panel',
		)
	);

	$footer_fields = array(
		'printarium_footer_about'    => array( __( 'Opis w stopce', 'printarium' ), 'textarea' ),
		'printarium_contact_email'   => array( __( 'E-mail', 'printarium' ), 'text' ),
		'printarium_contact_phone'   => array( __( 'Telefon', 'printarium' ), 'text' ),
		'printarium_contact_address' => array( __( 'Adres', 'printarium' ), 'text' ),
		'printarium_copyright'       => array( __( 'Tekst praw autorskich (puste = automatyczny)', 'printarium' ), 'text' ),
	);

	foreach ( $footer_fields as $key => $field ) {
		$wp_customize->add_setting(
			$key,
			array(
				'default'           => $defaults[ $key ],
				'sanitize_callback' => 'wp_kses_post',
				'transport'         => 'postMessage',
			)
		);
		$wp_customize->add_control(
			$key,
			array(
				'label'   => $field[0],
				'section' => 'printarium_footer',
				'type'    => $field[1],
			)
		);
	}
}
add_action( 'customize_register', 'printarium_customize_register' );

/**
 * Sanityzacja checkboxa.
 *
 * @param mixed $value Wartość.
 * @return bool
 */
function printarium_sanitize_checkbox( $value ) {
	return (bool) $value;
}
