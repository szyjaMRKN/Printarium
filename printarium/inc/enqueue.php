<?php
/**
 * Ładowanie stylów i skryptów.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Zwraca wersję pliku na podstawie czasu modyfikacji (cache busting w developmencie).
 *
 * @param string $relative_path Ścieżka względem katalogu motywu.
 * @return string
 */
function printarium_asset_version( $relative_path ) {
	$file = PRINTARIUM_DIR . ltrim( $relative_path, '/' );

	return file_exists( $file ) ? (string) filemtime( $file ) : PRINTARIUM_VERSION;
}

/**
 * Front-end.
 */
function printarium_enqueue_assets() {
	// Montserrat – zgodnie z systemem projektowym.
	if ( get_theme_mod( 'printarium_google_fonts', true ) ) {
		wp_enqueue_style(
			'printarium-fonts',
			'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap',
			array(),
			null // phpcs:ignore WordPress.WP.EnqueuedResourceParameters.MissingVersion
		);
	}

	wp_enqueue_style( 'printarium-style', get_stylesheet_uri(), array(), PRINTARIUM_VERSION );

	wp_enqueue_style(
		'printarium-main',
		PRINTARIUM_URI . 'assets/css/main.css',
		array( 'printarium-style' ),
		printarium_asset_version( 'assets/css/main.css' )
	);

	if ( printarium_is_woocommerce_active() ) {
		wp_enqueue_style(
			'printarium-woocommerce',
			PRINTARIUM_URI . 'assets/css/woocommerce.css',
			array( 'printarium-main' ),
			printarium_asset_version( 'assets/css/woocommerce.css' )
		);

		// Koszyk i zamówienie w nowych instalacjach WooCommerce budowane są
		// z bloków, które mają własną, jasną stylistykę.
		wp_enqueue_style(
			'printarium-wc-blocks',
			PRINTARIUM_URI . 'assets/css/wc-blocks.css',
			array( 'printarium-woocommerce' ),
			printarium_asset_version( 'assets/css/wc-blocks.css' )
		);
	}

	wp_enqueue_script(
		'printarium-main',
		PRINTARIUM_URI . 'assets/js/main.js',
		array(),
		printarium_asset_version( 'assets/js/main.js' ),
		true
	);

	wp_localize_script(
		'printarium-main',
		'printariumData',
		array(
			'ajaxUrl' => admin_url( 'admin-ajax.php' ),
			'i18n'    => array(
				'added'     => __( 'Produkt dodany do koszyka', 'printarium' ),
				'error'     => __( 'Nie udało się zapisać zmian', 'printarium' ),
				'closeMenu' => __( 'Zamknij menu', 'printarium' ),
				'openMenu'  => __( 'Otwórz menu', 'printarium' ),
			),
		)
	);

	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}
}
add_action( 'wp_enqueue_scripts', 'printarium_enqueue_assets' );

/**
 * Style panelu administracyjnego motywu.
 *
 * @param string $hook Aktualna podstrona.
 */
function printarium_admin_assets( $hook ) {
	if ( false === strpos( $hook, 'printarium' ) ) {
		return;
	}

	wp_enqueue_style(
		'printarium-admin',
		PRINTARIUM_URI . 'assets/css/admin.css',
		array(),
		printarium_asset_version( 'assets/css/admin.css' )
	);
}
add_action( 'admin_enqueue_scripts', 'printarium_admin_assets' );

/**
 * Preconnect do Google Fonts.
 *
 * @param array  $urls          Adresy.
 * @param string $relation_type Typ relacji.
 * @return array
 */
function printarium_resource_hints( $urls, $relation_type ) {
	if ( wp_style_is( 'printarium-fonts', 'queue' ) && 'preconnect' === $relation_type ) {
		$urls[] = array(
			'href'        => 'https://fonts.gstatic.com',
			'crossorigin',
		);
	}

	return $urls;
}
add_filter( 'wp_resource_hints', 'printarium_resource_hints', 10, 2 );
