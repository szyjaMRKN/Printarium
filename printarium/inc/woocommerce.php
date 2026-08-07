<?php
/**
 * Integracja z WooCommerce.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

if ( ! printarium_is_woocommerce_active() ) {
	return;
}

/* -------------------------------------------------------------------------
 * Układ strony sklepu – własne wrappery zamiast domyślnych.
 * ---------------------------------------------------------------------- */

remove_action( 'woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10 );
remove_action( 'woocommerce_after_main_content', 'woocommerce_output_content_wrapper_end', 10 );
remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );
remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar', 10 );

/**
 * Otwarcie kontenera treści sklepu.
 */
function printarium_wc_wrapper_start() {
	$is_product_list = is_shop() || is_product_taxonomy();
	$with_sidebar    = $is_product_list && is_active_sidebar( 'shop-sidebar' );
	?>
	<div class="shop-layout <?php echo $with_sidebar ? 'shop-layout--with-sidebar' : 'shop-layout--full'; ?>">
		<div class="container">
			<?php if ( $with_sidebar ) : ?>
				<aside class="shop-sidebar" id="shop-filters">
					<div class="shop-sidebar__inner">
						<div class="shop-sidebar__head">
							<h2 class="shop-sidebar__title"><?php echo printarium_get_icon( 'filter', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?> <?php esc_html_e( 'Filtry sklepu', 'printarium' ); ?></h2>
							<button type="button" class="shop-sidebar__close btn-icon" data-printarium-filters-close aria-label="<?php esc_attr_e( 'Zamknij filtry', 'printarium' ); ?>">
								<?php printarium_icon( 'close', 20 ); ?>
							</button>
						</div>
						<?php dynamic_sidebar( 'shop-sidebar' ); ?>
						<a class="btn btn--ghost shop-sidebar__reset" href="<?php echo esc_url( printarium_shop_base_url() ); ?>">
							<?php printarium_icon( 'refresh', 18 ); ?> <?php esc_html_e( 'Wyczyść filtry', 'printarium' ); ?>
						</a>
					</div>
				</aside>
			<?php endif; ?>
			<main id="primary" class="shop-main site-main">
	<?php
}
add_action( 'woocommerce_before_main_content', 'printarium_wc_wrapper_start', 10 );

/**
 * Zamknięcie kontenera treści sklepu.
 */
function printarium_wc_wrapper_end() {
	?>
			</main>
		</div>
	</div>
	<?php
}
add_action( 'woocommerce_after_main_content', 'printarium_wc_wrapper_end', 10 );

/**
 * Adres bazowy sklepu (bez parametrów filtrów).
 *
 * @return string
 */
function printarium_shop_base_url() {
	if ( is_product_taxonomy() ) {
		$term = get_queried_object();
		if ( $term instanceof WP_Term ) {
			return get_term_link( $term );
		}
	}

	$shop_id = wc_get_page_id( 'shop' );

	return $shop_id > 0 ? get_permalink( $shop_id ) : home_url( '/' );
}

/* -------------------------------------------------------------------------
 * Nagłówek archiwum sklepu.
 * ---------------------------------------------------------------------- */

remove_action( 'woocommerce_archive_description', 'woocommerce_taxonomy_archive_description', 10 );
remove_action( 'woocommerce_archive_description', 'woocommerce_product_archive_description', 10 );

/**
 * Nagłówek nad listą produktów: okruszki, tytuł, opis.
 */
function printarium_shop_header() {
	if ( ! is_shop() && ! is_product_taxonomy() ) {
		return;
	}

	$description = '';

	if ( is_product_taxonomy() ) {
		$term = get_queried_object();
		if ( $term instanceof WP_Term ) {
			$description = $term->description;
		}
	} elseif ( is_shop() && is_post_type_archive( 'product' ) ) {
		$shop_page = get_post( wc_get_page_id( 'shop' ) );
		if ( $shop_page ) {
			$description = $shop_page->post_content;
		}
	}
	?>
	<header class="shop-header">
		<?php printarium_breadcrumbs(); ?>
		<h1 class="shop-header__title"><?php woocommerce_page_title(); ?></h1>
		<?php if ( $description ) : ?>
			<div class="shop-header__description"><?php echo wp_kses_post( wpautop( do_shortcode( $description ) ) ); ?></div>
		<?php endif; ?>
	</header>
	<?php
}
add_action( 'woocommerce_before_shop_loop', 'printarium_shop_header', 5 );

// Domyślny tytuł strony wyłączamy – mamy własny nagłówek.
add_filter( 'woocommerce_show_page_title', '__return_false' );

/**
 * Okruszki nad kartą produktu (na listach renderuje je nagłówek sklepu).
 */
function printarium_single_product_breadcrumbs() {
	if ( ! is_product() ) {
		return;
	}

	echo '<div class="single-product__breadcrumbs">';
	printarium_breadcrumbs();
	echo '</div>';
}
add_action( 'woocommerce_before_main_content', 'printarium_single_product_breadcrumbs', 15 );

/**
 * Pasek narzędzi nad listą: licznik + sortowanie + przełącznik widoku.
 */
function printarium_shop_toolbar_open() {
	if ( ! is_shop() && ! is_product_taxonomy() ) {
		return;
	}
	echo '<div class="shop-toolbar">';
	echo '<button type="button" class="btn btn--secondary shop-toolbar__filters" data-printarium-filters-open>' . printarium_get_icon( 'filter', 18 ) . ' ' . esc_html__( 'Filtry', 'printarium' ) . '</button>';
	echo '<div class="shop-toolbar__meta">';
}
add_action( 'woocommerce_before_shop_loop', 'printarium_shop_toolbar_open', 18 );

/**
 * Zamknięcie paska narzędzi + przełącznik siatka/lista.
 */
function printarium_shop_toolbar_close() {
	if ( ! is_shop() && ! is_product_taxonomy() ) {
		return;
	}
	?>
		</div>
		<div class="shop-toolbar__view" role="group" aria-label="<?php esc_attr_e( 'Widok produktów', 'printarium' ); ?>">
			<button type="button" class="view-toggle is-active" data-printarium-view="grid" aria-pressed="true" aria-label="<?php esc_attr_e( 'Widok siatki', 'printarium' ); ?>">
				<?php printarium_icon( 'grid', 20 ); ?>
			</button>
			<button type="button" class="view-toggle" data-printarium-view="list" aria-pressed="false" aria-label="<?php esc_attr_e( 'Widok listy', 'printarium' ); ?>">
				<?php printarium_icon( 'list', 20 ); ?>
			</button>
		</div>
	</div>
	<?php
}
add_action( 'woocommerce_before_shop_loop', 'printarium_shop_toolbar_close', 31 );

/**
 * Liczba produktów na stronę.
 *
 * @return int
 */
function printarium_products_per_page() {
	return 12;
}
add_filter( 'loop_shop_per_page', 'printarium_products_per_page', 20 );

/**
 * Liczba kolumn w siatce.
 *
 * @return int
 */
function printarium_loop_columns() {
	return 4;
}
add_filter( 'loop_shop_columns', 'printarium_loop_columns', 20 );

/* -------------------------------------------------------------------------
 * Karta produktu w pętli.
 * ---------------------------------------------------------------------- */

// Karta budowana jest w całości przez motyw – domyślny link opakowujący
// oraz miniatura WooCommerce muszą zostać wyłączone, inaczej zdjęcie
// renderowałoby się dwukrotnie, a przycisk trafiłby wewnątrz znacznika <a>.
remove_action( 'woocommerce_before_shop_loop_item', 'woocommerce_template_loop_product_link_open', 10 );
remove_action( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_product_link_close', 5 );
remove_action( 'woocommerce_before_shop_loop_item_title', 'woocommerce_template_loop_product_thumbnail', 10 );
remove_action( 'woocommerce_before_shop_loop_item_title', 'woocommerce_show_product_loop_sale_flash', 10 );
remove_action( 'woocommerce_shop_loop_item_title', 'woocommerce_template_loop_product_title', 10 );
remove_action( 'woocommerce_after_shop_loop_item_title', 'woocommerce_template_loop_rating', 5 );
remove_action( 'woocommerce_after_shop_loop_item_title', 'woocommerce_template_loop_price', 10 );
remove_action( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_add_to_cart', 10 );

/**
 * Otwiera kontener karty i renderuje media (zdjęcie + badge + ulubione).
 */
function printarium_loop_card_media() {
	global $product;
	?>
	<div class="product-card__media">
		<?php printarium_product_badges( $product ); ?>
		<a class="product-card__link" href="<?php the_permalink(); ?>" aria-label="<?php echo esc_attr( $product->get_name() ); ?>">
			<?php echo woocommerce_get_product_thumbnail( 'printarium-card' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
		</a>
		<button type="button" class="product-card__wishlist" data-printarium-wishlist="<?php echo esc_attr( $product->get_id() ); ?>" aria-pressed="false" aria-label="<?php esc_attr_e( 'Dodaj do ulubionych', 'printarium' ); ?>">
			<?php printarium_icon( 'heart', 22 ); ?>
		</button>
	</div>
	<div class="product-card__body">
	<?php
}
add_action( 'woocommerce_before_shop_loop_item_title', 'printarium_loop_card_media', 9 );

/**
 * Tytuł produktu jako link.
 */
function printarium_loop_title() {
	echo '<h2 class="product-card__title"><a href="' . esc_url( get_permalink() ) . '">' . esc_html( get_the_title() ) . '</a></h2>';
}
add_action( 'woocommerce_shop_loop_item_title', 'printarium_loop_title', 10 );

/**
 * Ocena w postaci gwiazdek + liczba opinii.
 */
function printarium_loop_rating() {
	global $product;

	$count   = $product->get_review_count();
	$average = (float) $product->get_average_rating();

	if ( ! wc_review_ratings_enabled() ) {
		return;
	}

	echo '<div class="product-card__rating">';
	echo '<span class="rating-stars" aria-hidden="true">';
	for ( $i = 1; $i <= 5; $i++ ) {
		$class = $i <= round( $average ) ? 'is-filled' : '';
		echo '<span class="rating-stars__star ' . esc_attr( $class ) . '">' . printarium_get_icon( 'star', 16 ) . '</span>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	}
	echo '</span>';
	echo '<span class="product-card__reviews">(' . esc_html( (string) $count ) . ')</span>';
	echo '</div>';
}
add_action( 'woocommerce_after_shop_loop_item_title', 'printarium_loop_rating', 5 );

/**
 * Cena + status dostępności.
 */
function printarium_loop_price() {
	global $product;

	echo '<div class="product-card__price">' . wp_kses_post( $product->get_price_html() ) . '</div>';
	printarium_stock_status( $product );
}
add_action( 'woocommerce_after_shop_loop_item_title', 'printarium_loop_price', 10 );

/**
 * Chipsy z atrybutami (kolor / materiał / typ).
 */
function printarium_loop_attributes() {
	global $product;

	$chips = printarium_product_chips( $product );

	if ( empty( $chips ) ) {
		echo '</div>'; // .product-card__body
		return;
	}

	echo '<ul class="product-card__chips">';
	foreach ( $chips as $chip ) {
		echo '<li class="chip chip--static">';
		if ( ! empty( $chip['swatch'] ) ) {
			echo '<span class="chip__swatch" style="--chip-color:' . esc_attr( $chip['swatch'] ) . '"></span>';
		} elseif ( ! empty( $chip['icon'] ) ) {
			echo printarium_get_icon( $chip['icon'], 14 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		}
		echo '<span class="chip__label">' . esc_html( $chip['label'] ) . '</span>';
		echo '</li>';
	}
	echo '</ul>';
	echo '</div>'; // .product-card__body
}
add_action( 'woocommerce_after_shop_loop_item_title', 'printarium_loop_attributes', 20 );

/**
 * Przycisk „Dodaj do koszyka” na dole karty.
 */
function printarium_loop_add_to_cart() {
	echo '<div class="product-card__footer">';
	woocommerce_template_loop_add_to_cart();
	echo '</div>';
}
add_action( 'woocommerce_after_shop_loop_item', 'printarium_loop_add_to_cart', 10 );

/**
 * Klasy i treść przycisku dodania do koszyka.
 *
 * @param array      $args    Argumenty.
 * @param WC_Product $product Produkt.
 * @return array
 */
function printarium_add_to_cart_args( $args, $product ) {
	$args['class'] = implode(
		' ',
		array_filter(
			array(
				'btn',
				'btn--primary',
				'product-card__button',
				$product->is_purchasable() && $product->is_in_stock() ? 'add_to_cart_button' : '',
				$product->supports( 'ajax_add_to_cart' ) && $product->is_purchasable() && $product->is_in_stock() ? 'ajax_add_to_cart' : '',
			)
		)
	);

	return $args;
}
add_filter( 'woocommerce_loop_add_to_cart_args', 'printarium_add_to_cart_args', 10, 2 );

/**
 * Ikona koszyka w przycisku pętli.
 *
 * @param string     $html    HTML linku.
 * @param WC_Product $product Produkt.
 * @param array      $args    Argumenty.
 * @return string
 */
function printarium_add_to_cart_link( $html, $product, $args ) {
	if ( ! $product->is_in_stock() ) {
		return $html;
	}

	// Wstawia ikonę koszyka zaraz za otwierającym znacznikiem <a>.
	return preg_replace( '/(<a\b[^>]*>)/', '$1' . printarium_get_icon( 'cart', 20 ), $html, 1 );
}
add_filter( 'woocommerce_loop_add_to_cart_link', 'printarium_add_to_cart_link', 10, 3 );

/* -------------------------------------------------------------------------
 * Pomocnicze: badge, status magazynowy, chipsy.
 * ---------------------------------------------------------------------- */

/**
 * Wyświetla plakietki produktu (Nowość / Promocja / Brak w magazynie).
 *
 * @param WC_Product $product Produkt.
 */
function printarium_product_badges( $product ) {
	$badges = array();

	if ( ! $product->is_in_stock() ) {
		$badges[] = array( 'label' => __( 'Brak w magazynie', 'printarium' ), 'class' => 'badge--muted' );
	} elseif ( $product->is_on_sale() ) {
		$badges[] = array( 'label' => __( 'Promocja', 'printarium' ), 'class' => 'badge--sale' );
	}

	$days_new = (int) apply_filters( 'printarium_new_product_days', 30 );
	$created  = $product->get_date_created();

	if ( $created && ( time() - $created->getTimestamp() ) < ( $days_new * DAY_IN_SECONDS ) ) {
		array_unshift( $badges, array( 'label' => __( 'Nowość', 'printarium' ), 'class' => 'badge--new' ) );
	}

	if ( empty( $badges ) ) {
		return;
	}

	echo '<div class="product-card__badges">';
	foreach ( $badges as $badge ) {
		echo '<span class="badge ' . esc_attr( $badge['class'] ) . '">' . esc_html( $badge['label'] ) . '</span>';
	}
	echo '</div>';
}

/**
 * Kropka statusu dostępności zgodna z systemem projektowym.
 *
 * @param WC_Product $product Produkt.
 */
function printarium_stock_status( $product ) {
	if ( ! $product->is_in_stock() ) {
		$class = 'is-unavailable';
		$label = __( 'Niedostępny', 'printarium' );
	} elseif ( $product->managing_stock() && $product->get_stock_quantity() !== null && $product->get_stock_quantity() <= (int) get_option( 'woocommerce_notify_low_stock_amount', 2 ) ) {
		$class = 'is-low';
		$label = __( 'Ostatnie sztuki', 'printarium' );
	} else {
		$class = 'is-available';
		$label = __( 'Dostępny', 'printarium' );
	}

	echo '<p class="stock-status ' . esc_attr( $class ) . '"><span class="stock-status__dot" aria-hidden="true"></span>' . esc_html( $label ) . '</p>';
}

/**
 * Zwraca do trzech atrybutów produktu jako chipsy.
 *
 * @param WC_Product $product Produkt.
 * @return array
 */
function printarium_product_chips( $product ) {
	$chips    = array();
	$swatches = apply_filters(
		'printarium_color_swatches',
		array(
			'czarny'       => '#141414',
			'czarne'       => '#141414',
			'bialy'        => '#F3F4EF',
			'biały'        => '#F3F4EF',
			'zielony'      => '#829B2F',
			'transparentny' => 'rgba(243,244,239,.35)',
			'przezroczysty' => 'rgba(243,244,239,.35)',
		)
	);

	foreach ( $product->get_attributes() as $attribute ) {
		if ( count( $chips ) >= 3 ) {
			break;
		}

		$name   = $attribute->get_name();
		$values = array();

		if ( $attribute->is_taxonomy() ) {
			$terms = wc_get_product_terms( $product->get_id(), $name, array( 'fields' => 'names' ) );
			$values = is_array( $terms ) ? $terms : array();
		} else {
			$values = $attribute->get_options();
		}

		if ( empty( $values ) ) {
			continue;
		}

		$label = (string) reset( $values );
		$key   = mb_strtolower( $label );
		$chip  = array( 'label' => $label );

		if ( isset( $swatches[ $key ] ) ) {
			$chip['swatch'] = $swatches[ $key ];
		} elseif ( false !== stripos( $name, 'material' ) || false !== stripos( $name, 'materiał' ) ) {
			$chip['icon'] = 'box';
		}

		$chips[] = $chip;
	}

	return $chips;
}

/* -------------------------------------------------------------------------
 * Koszyk w nagłówku – fragmenty AJAX.
 * ---------------------------------------------------------------------- */

/**
 * Renderuje przycisk koszyka w nagłówku.
 *
 * @return string
 */
function printarium_get_cart_button() {
	$count = WC()->cart ? WC()->cart->get_cart_contents_count() : 0;

	ob_start();
	?>
	<a class="header-action header-action--cart" href="<?php echo esc_url( wc_get_cart_url() ); ?>" data-printarium-minicart-open aria-label="<?php esc_attr_e( 'Twój koszyk', 'printarium' ); ?>">
		<?php printarium_icon( 'cart', 24 ); ?>
		<span class="header-action__count<?php echo $count ? '' : ' is-empty'; ?>"><?php echo esc_html( (string) $count ); ?></span>
	</a>
	<?php
	return ob_get_clean();
}

/**
 * Odświeżanie licznika koszyka przez AJAX.
 *
 * @param array $fragments Fragmenty.
 * @return array
 */
function printarium_cart_fragments( $fragments ) {
	$fragments['a.header-action--cart'] = printarium_get_cart_button();

	return $fragments;
}
add_filter( 'woocommerce_add_to_cart_fragments', 'printarium_cart_fragments' );

/* -------------------------------------------------------------------------
 * Drobne poprawki UX.
 * ---------------------------------------------------------------------- */

/**
 * Pasek zaufania pod przyciskiem „Dodaj do koszyka”.
 */
function printarium_product_trust_bar() {
	$items = apply_filters(
		'printarium_product_trust_items',
		array(
			array( 'icon' => 'truck', 'text' => __( 'Wysyłka w 1–3 dni robocze', 'printarium' ) ),
			array( 'icon' => 'shield', 'text' => __( 'Bezpieczne dla zwierząt', 'printarium' ) ),
			array( 'icon' => 'pencil', 'text' => __( 'Możliwa personalizacja', 'printarium' ) ),
		)
	);

	if ( empty( $items ) ) {
		return;
	}

	echo '<div class="product-trust">';
	foreach ( $items as $item ) {
		echo '<div class="product-trust__item">' . printarium_get_icon( $item['icon'], 22 ) . '<span>' . esc_html( $item['text'] ) . '</span></div>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	}
	echo '</div>';
}
add_action( 'woocommerce_single_product_summary', 'printarium_product_trust_bar', 35 );

/**
 * Status dostępności na karcie produktu (pod ceną).
 */
function printarium_single_stock_status() {
	global $product;

	if ( $product instanceof WC_Product ) {
		printarium_stock_status( $product );
	}
}
add_action( 'woocommerce_single_product_summary', 'printarium_single_stock_status', 11 );

/**
 * Powiązane produkty – 4 sztuki w jednym rzędzie.
 *
 * @param array $args Argumenty.
 * @return array
 */
function printarium_related_products_args( $args ) {
	$args['posts_per_page'] = 4;
	$args['columns']        = 4;

	return $args;
}
add_filter( 'woocommerce_output_related_products_args', 'printarium_related_products_args', 20 );

/**
 * Placeholder dla produktów bez zdjęcia.
 *
 * @return string
 */
function printarium_placeholder_img_src() {
	return PRINTARIUM_URI . 'assets/images/placeholder.svg';
}
add_filter( 'woocommerce_placeholder_img_src', 'printarium_placeholder_img_src' );

/**
 * Etykieta pola wyszukiwania produktów.
 *
 * @param array $args Argumenty formularza.
 * @return array
 */
function printarium_product_search_form_args( $args ) {
	$args['placeholder'] = __( 'Szukaj produktów…', 'printarium' );

	return $args;
}
add_filter( 'woocommerce_product_search_form_args', 'printarium_product_search_form_args' );

add_filter( 'woocommerce_kses_notice_allowed_tags', 'printarium_notice_allowed_tags' );

/**
 * Zezwala na SVG w komunikatach WooCommerce (ikony statusów).
 *
 * @param array $tags Dozwolone tagi.
 * @return array
 */
function printarium_notice_allowed_tags( $tags ) {
	$tags['svg']    = array(
		'class'            => true,
		'width'            => true,
		'height'           => true,
		'viewbox'          => true,
		'fill'             => true,
		'stroke'           => true,
		'stroke-width'     => true,
		'stroke-linecap'   => true,
		'stroke-linejoin'  => true,
		'aria-hidden'      => true,
		'focusable'        => true,
		'role'             => true,
	);
	$tags['path']   = array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true );
	$tags['circle'] = array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true, 'stroke' => true );
	$tags['rect']   = array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true );
	$tags['span']   = array( 'class' => true );

	return $tags;
}
