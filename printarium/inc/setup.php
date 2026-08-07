<?php
/**
 * Konfiguracja motywu: wsparcie funkcji, menu, obszary widgetów.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Rejestruje wsparcie dla funkcji WordPressa.
 */
function printarium_setup() {
	load_theme_textdomain( 'printarium', PRINTARIUM_DIR . 'languages' );

	add_theme_support( 'automatic-feed-links' );
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'customize-selective-refresh-widgets' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'align-wide' );
	add_theme_support( 'editor-styles' );
	add_editor_style( 'assets/css/editor.css' );

	add_theme_support(
		'html5',
		array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script', 'navigation-widgets' )
	);

	add_theme_support(
		'custom-logo',
		array(
			'height'      => 48,
			'width'       => 220,
			'flex-height' => true,
			'flex-width'  => true,
		)
	);

	// WooCommerce.
	add_theme_support(
		'woocommerce',
		array(
			'thumbnail_image_width' => 600,
			'single_image_width'    => 1200,
			'product_grid'          => array(
				'default_rows'    => 3,
				'min_rows'        => 1,
				'default_columns' => 4,
				'min_columns'     => 2,
				'max_columns'     => 4,
			),
		)
	);
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );

	register_nav_menus(
		array(
			'primary' => __( 'Menu główne', 'printarium' ),
			'footer'  => __( 'Menu w stopce', 'printarium' ),
			'legal'   => __( 'Menu prawne (dół stopki)', 'printarium' ),
		)
	);

	// Rozmiary obrazków dopasowane do siatki motywu.
	add_image_size( 'printarium-card', 720, 720, true );
	add_image_size( 'printarium-tile', 960, 1200, true );
	add_image_size( 'printarium-hero', 1920, 1200, true );
}
add_action( 'after_setup_theme', 'printarium_setup' );

/**
 * Szerokość treści.
 */
function printarium_content_width() {
	$GLOBALS['content_width'] = apply_filters( 'printarium_content_width', 1200 );
}
add_action( 'after_setup_theme', 'printarium_content_width', 0 );

/**
 * Obszary widgetów.
 */
function printarium_widgets_init() {
	register_sidebar(
		array(
			'name'          => __( 'Sidebar sklepu', 'printarium' ),
			'id'            => 'shop-sidebar',
			'description'   => __( 'Filtry i widgety widoczne na stronach sklepu.', 'printarium' ),
			'before_widget' => '<section id="%1$s" class="widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h3 class="widget__title">',
			'after_title'   => '</h3>',
		)
	);

	for ( $i = 1; $i <= 3; $i++ ) {
		register_sidebar(
			array(
				/* translators: %d: numer kolumny stopki. */
				'name'          => sprintf( __( 'Stopka – kolumna %d', 'printarium' ), $i ),
				'id'            => 'footer-' . $i,
				'before_widget' => '<section id="%1$s" class="widget %2$s">',
				'after_widget'  => '</section>',
				'before_title'  => '<h3 class="widget__title">',
				'after_title'   => '</h3>',
			)
		);
	}
}
add_action( 'widgets_init', 'printarium_widgets_init' );

/**
 * Klasy body.
 *
 * @param array $classes Klasy.
 * @return array
 */
function printarium_body_classes( $classes ) {
	$classes[] = 'printarium';

	if ( ! is_active_sidebar( 'shop-sidebar' ) ) {
		$classes[] = 'no-shop-sidebar';
	}

	if ( function_exists( 'is_woocommerce' ) && ( is_woocommerce() || is_cart() || is_checkout() || is_account_page() ) ) {
		$classes[] = 'is-shop';
	}

	return $classes;
}
add_filter( 'body_class', 'printarium_body_classes' );

/**
 * Wyłącza emoji – niepotrzebne żądania na froncie.
 */
function printarium_disable_emojis() {
	remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
	remove_action( 'wp_print_styles', 'print_emoji_styles' );
}
add_action( 'init', 'printarium_disable_emojis' );

/**
 * Wskazuje motywowi, że obsługuje HPOS WooCommerce.
 */
function printarium_declare_wc_compat() {
	if ( class_exists( \Automattic\WooCommerce\Utilities\FeaturesUtil::class ) ) {
		\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility( 'custom_order_tables', __FILE__, true );
	}
}
add_action( 'before_woocommerce_init', 'printarium_declare_wc_compat' );
