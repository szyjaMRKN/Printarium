<?php
/**
 * Funkcje pomocnicze szablonów.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Czy WooCommerce jest aktywne.
 *
 * @return bool
 */
function printarium_is_woocommerce_active() {
	return class_exists( 'WooCommerce' );
}

/**
 * Logo sklepu – własne logo lub znak Printarium (SVG) z nazwą serwisu.
 */
function printarium_site_branding() {
	$url = home_url( '/' );

	echo '<a class="site-brand" href="' . esc_url( $url ) . '" rel="home">';

	if ( has_custom_logo() ) {
		$logo_id = get_theme_mod( 'custom_logo' );
		echo wp_get_attachment_image( $logo_id, 'full', false, array( 'class' => 'site-brand__logo', 'alt' => esc_attr( get_bloginfo( 'name' ) ) ) );
	} else {
		echo printarium_get_brand_mark(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		echo '<span class="site-brand__name">' . esc_html( get_bloginfo( 'name' ) ) . '</span>';
	}

	echo '</a>';
}

/**
 * Heksagonalny znak marki (mrówka w laboratoryjnej kolbie – uproszczona forma).
 *
 * @return string
 */
function printarium_get_brand_mark() {
	ob_start();
	?>
	<svg class="site-brand__mark" width="44" height="44" viewBox="0 0 48 48" fill="none" aria-hidden="true" focusable="false">
		<path d="M24 3.4 41.8 13.7v20.6L24 44.6 6.2 34.3V13.7L24 3.4Z" fill="#0D1913" stroke="#829B2F" stroke-width="2"/>
		<path d="M20.5 12.5h7" stroke="#F3F4EF" stroke-width="1.8" stroke-linecap="round"/>
		<path d="M22 12.8v5.4l-4.2 7.6" stroke="#F3F4EF" stroke-width="1.8" stroke-linecap="round"/>
		<path d="M26 12.8v5.4l4.2 7.6" stroke="#F3F4EF" stroke-width="1.8" stroke-linecap="round"/>
		<ellipse cx="24" cy="31" rx="3.6" ry="4.6" fill="#829B2F"/>
		<circle cx="24" cy="24.6" r="2.4" fill="#829B2F"/>
		<circle cx="24" cy="20.2" r="1.8" fill="#829B2F"/>
		<path d="M20.4 24.6 16 21.8M20.4 27.4 15.8 28M20.6 30.6 16.6 33.4M27.6 24.6 32 21.8M27.6 27.4 32.2 28M27.4 30.6 31.4 33.4" stroke="#829B2F" stroke-width="1.5" stroke-linecap="round"/>
		<path d="m23 18.6-1.8-2.2M25 18.6l1.8-2.2" stroke="#829B2F" stroke-width="1.5" stroke-linecap="round"/>
	</svg>
	<?php
	return ob_get_clean();
}

/**
 * Ikona kategorii wg slugu (fallback: box).
 *
 * @param string $slug Slug kategorii.
 * @return string
 */
function printarium_category_icon_name( $slug ) {
	$map = array(
		'terraria'            => 'leaf',
		'terraria-plus'       => 'flask',
		'formikaria-i-areny'  => 'box',
		'formikaria'          => 'box',
		'areny'               => 'grid',
		'zwierzeta'           => 'paw',
		'akcesoria'           => 'flask',
		'na-zamowienie'       => 'pencil',
	);

	return isset( $map[ $slug ] ) ? $map[ $slug ] : 'box';
}

/**
 * Nagłówek strony (tytuł + opis + okruszki).
 *
 * @param array $args title, subtitle, breadcrumbs (bool).
 */
function printarium_page_hero( $args = array() ) {
	$args = wp_parse_args(
		$args,
		array(
			'title'       => get_the_title(),
			'subtitle'    => '',
			'breadcrumbs' => true,
			'class'       => '',
		)
	);
	?>
	<header class="page-hero <?php echo esc_attr( $args['class'] ); ?>">
		<div class="container">
			<?php
			if ( $args['breadcrumbs'] ) {
				printarium_breadcrumbs();
			}
			?>
			<h1 class="page-hero__title"><?php echo wp_kses_post( $args['title'] ); ?></h1>
			<?php if ( $args['subtitle'] ) : ?>
				<p class="page-hero__subtitle"><?php echo wp_kses_post( $args['subtitle'] ); ?></p>
			<?php endif; ?>
		</div>
	</header>
	<?php
}

/**
 * Okruszki (breadcrumb) – korzysta z WooCommerce, jeśli dostępne.
 */
function printarium_breadcrumbs() {
	if ( is_front_page() ) {
		return;
	}

	if ( printarium_is_woocommerce_active() && ( is_woocommerce() || is_cart() || is_checkout() ) ) {
		woocommerce_breadcrumb(
			array(
				'delimiter'   => '<span class="breadcrumb__sep" aria-hidden="true">/</span>',
				'wrap_before' => '<nav class="breadcrumb" aria-label="' . esc_attr__( 'Ścieżka nawigacji', 'printarium' ) . '">',
				'wrap_after'  => '</nav>',
			)
		);
		return;
	}

	echo '<nav class="breadcrumb" aria-label="' . esc_attr__( 'Ścieżka nawigacji', 'printarium' ) . '">';
	echo '<a href="' . esc_url( home_url( '/' ) ) . '">' . esc_html__( 'Strona główna', 'printarium' ) . '</a>';
	echo '<span class="breadcrumb__sep" aria-hidden="true">/</span>';

	if ( is_singular() ) {
		echo '<span class="breadcrumb__current">' . esc_html( get_the_title() ) . '</span>';
	} elseif ( is_search() ) {
		echo '<span class="breadcrumb__current">' . esc_html__( 'Wyniki wyszukiwania', 'printarium' ) . '</span>';
	} elseif ( is_404() ) {
		echo '<span class="breadcrumb__current">' . esc_html__( 'Nie znaleziono strony', 'printarium' ) . '</span>';
	} else {
		echo '<span class="breadcrumb__current">' . wp_kses_post( get_the_archive_title() ) . '</span>';
	}

	echo '</nav>';
}

/**
 * Paginacja w stylu systemu projektowego.
 *
 * @param WP_Query|null $query Zapytanie.
 */
function printarium_pagination( $query = null ) {
	global $wp_query;
	$query = $query ? $query : $wp_query;

	if ( $query->max_num_pages < 2 ) {
		return;
	}

	$links = paginate_links(
		array(
			'total'     => $query->max_num_pages,
			'current'   => max( 1, get_query_var( 'paged' ) ? get_query_var( 'paged' ) : 1 ),
			'type'      => 'array',
			'mid_size'  => 1,
			'end_size'  => 1,
			'prev_text' => printarium_get_icon( 'arrow-left', 18 ),
			'next_text' => printarium_get_icon( 'arrow-right', 18 ),
		)
	);

	if ( ! $links ) {
		return;
	}

	echo '<nav class="pagination" aria-label="' . esc_attr__( 'Paginacja', 'printarium' ) . '"><ul class="pagination__list">';
	foreach ( $links as $link ) {
		echo '<li class="pagination__item">' . wp_kses_post( $link ) . '</li>';
	}
	echo '</ul></nav>';
}

/**
 * Zwraca listę głównych kategorii sklepu do sekcji kafelków.
 *
 * @param int $limit Ile kategorii.
 * @return array
 */
function printarium_get_shop_categories( $limit = 5 ) {
	if ( ! printarium_is_woocommerce_active() ) {
		return array();
	}

	$terms = get_terms(
		array(
			'taxonomy'   => 'product_cat',
			'hide_empty' => false,
			'parent'     => 0,
			'number'     => $limit,
			'exclude'    => array( get_option( 'default_product_cat' ) ),
			'orderby'    => 'menu_order',
		)
	);

	return is_wp_error( $terms ) ? array() : $terms;
}

/**
 * Zdjęcie kategorii (miniatura WooCommerce lub placeholder).
 *
 * @param WP_Term $term Kategoria.
 * @param string  $size Rozmiar.
 * @return string HTML.
 */
function printarium_category_thumbnail( $term, $size = 'printarium-card' ) {
	$thumb_id = get_term_meta( $term->term_id, 'thumbnail_id', true );

	if ( $thumb_id ) {
		return wp_get_attachment_image( $thumb_id, $size, false, array( 'class' => 'category-card__image', 'loading' => 'lazy' ) );
	}

	return '<span class="category-card__placeholder">' . printarium_get_icon( printarium_category_icon_name( $term->slug ), 48 ) . '</span>';
}

/**
 * Zastępcze menu, gdy użytkownik nie przypisał jeszcze menu do lokalizacji.
 *
 * @param array $args Argumenty wp_nav_menu().
 */
function printarium_menu_fallback( $args ) {
	$class = isset( $args['menu_class'] ) ? $args['menu_class'] : 'primary-nav__list';
	$items = array();

	foreach ( printarium_get_shop_categories( 5 ) as $term ) {
		$items[] = array(
			'url'   => get_term_link( $term ),
			'label' => $term->name,
		);
	}

	if ( empty( $items ) ) {
		$items[] = array(
			'url'   => home_url( '/' ),
			'label' => __( 'Strona główna', 'printarium' ),
		);
	}

	$oferta = get_page_by_path( 'oferta' );
	if ( $oferta ) {
		$items[] = array(
			'url'   => get_permalink( $oferta ),
			'label' => __( 'Oferta', 'printarium' ),
		);
	}

	$kontakt = get_page_by_path( 'kontakt' );
	if ( $kontakt ) {
		$items[] = array(
			'url'   => get_permalink( $kontakt ),
			'label' => __( 'Kontakt', 'printarium' ),
		);
	}

	echo '<ul class="' . esc_attr( $class ) . '">';
	foreach ( $items as $item ) {
		if ( is_wp_error( $item['url'] ) ) {
			continue;
		}
		echo '<li class="menu-item"><a href="' . esc_url( $item['url'] ) . '">' . esc_html( $item['label'] ) . '</a></li>';
	}
	echo '</ul>';
}

/**
 * Nagłówek sekcji na stronie głównej.
 *
 * @param string $title    Tytuł.
 * @param string $subtitle Podtytuł.
 */
function printarium_section_head( $title, $subtitle = '' ) {
	echo '<div class="section-head">';
	echo '<h2 class="section-head__title">' . wp_kses_post( $title ) . '</h2>';
	if ( $subtitle ) {
		echo '<p class="section-head__subtitle">' . wp_kses_post( $subtitle ) . '</p>';
	}
	echo '</div>';
}
