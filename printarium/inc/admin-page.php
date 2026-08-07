<?php
/**
 * Panel motywu: „Wygląd → Printarium”.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Rejestruje podstronę w menu Wygląd.
 */
function printarium_admin_menu() {
	add_theme_page(
		__( 'Printarium – konfiguracja', 'printarium' ),
		__( 'Printarium', 'printarium' ),
		'manage_options',
		'printarium',
		'printarium_admin_page'
	);
}
add_action( 'admin_menu', 'printarium_admin_menu' );

/**
 * Obsługa akcji importu / usuwania.
 */
function printarium_handle_admin_actions() {
	if ( ! isset( $_POST['printarium_action'] ) || ! current_user_can( 'manage_options' ) ) {
		return;
	}

	check_admin_referer( 'printarium_admin' );

	$action = sanitize_key( wp_unslash( $_POST['printarium_action'] ) );
	$log    = array();

	if ( 'import' === $action ) {
		$steps = isset( $_POST['printarium_steps'] ) ? array_map( 'sanitize_key', (array) wp_unslash( $_POST['printarium_steps'] ) ) : array();
		$log   = printarium_run_demo_import( $steps );
	} elseif ( 'remove' === $action ) {
		$log = array( printarium_remove_demo_content() );
	}

	set_transient( 'printarium_admin_log', $log, 60 );

	wp_safe_redirect( admin_url( 'themes.php?page=printarium&done=1' ) );
	exit;
}
add_action( 'admin_init', 'printarium_handle_admin_actions' );

/**
 * Widok podstrony.
 */
function printarium_admin_page() {
	$log        = get_transient( 'printarium_admin_log' );
	$wc_active  = printarium_is_woocommerce_active();
	$categories = $wc_active ? wp_count_terms( array( 'taxonomy' => 'product_cat', 'hide_empty' => false ) ) : 0;
	$products   = $wc_active ? wp_count_posts( 'product' ) : null;

	if ( $log ) {
		delete_transient( 'printarium_admin_log' );
	}
	?>
	<div class="wrap printarium-admin">

		<h1><?php esc_html_e( 'Printarium – konfiguracja motywu', 'printarium' ); ?></h1>
		<p class="printarium-admin__lead">
			<?php esc_html_e( 'Ta strona pozwala jednym kliknięciem utworzyć strukturę sklepu: kategorie, przykładowe produkty, podstrony i menu. Wszystko można później swobodnie edytować lub usunąć.', 'printarium' ); ?>
		</p>

		<?php if ( ! empty( $log ) ) : ?>
			<div class="notice notice-success">
				<?php foreach ( (array) $log as $line ) : ?>
					<p><?php echo esc_html( $line ); ?></p>
				<?php endforeach; ?>
			</div>
		<?php endif; ?>

		<?php if ( ! $wc_active ) : ?>
			<div class="notice notice-warning">
				<p>
					<strong><?php esc_html_e( 'WooCommerce nie jest aktywne.', 'printarium' ); ?></strong>
					<?php esc_html_e( 'Zainstaluj i włącz wtyczkę WooCommerce, aby korzystać z funkcji sklepu. Bez niej motyw działa jak zwykła strona firmowa.', 'printarium' ); ?>
					<a href="<?php echo esc_url( admin_url( 'plugin-install.php?s=woocommerce&tab=search&type=term' ) ); ?>"><?php esc_html_e( 'Zainstaluj WooCommerce', 'printarium' ); ?></a>
				</p>
			</div>
		<?php endif; ?>

		<div class="printarium-admin__grid">

			<div class="printarium-card">
				<h2><?php esc_html_e( '1. Import przykładowej zawartości', 'printarium' ); ?></h2>
				<p><?php esc_html_e( 'Zaznacz elementy, które mają zostać utworzone. Import jest bezpieczny do powtarzania – istniejące wpisy są pomijane, nie nadpisywane.', 'printarium' ); ?></p>

				<form method="post">
					<?php wp_nonce_field( 'printarium_admin' ); ?>
					<input type="hidden" name="printarium_action" value="import">

					<ul class="printarium-steps">
						<li><label><input type="checkbox" name="printarium_steps[]" value="categories" checked> <?php esc_html_e( 'Kategorie sklepu (Terraria, Terraria plus, Formikaria i areny, Zwierzęta, Akcesoria)', 'printarium' ); ?></label></li>
						<li><label><input type="checkbox" name="printarium_steps[]" value="attributes" checked> <?php esc_html_e( 'Atrybuty produktów (kolor, materiał, rozmiar)', 'printarium' ); ?></label></li>
						<li><label><input type="checkbox" name="printarium_steps[]" value="products" checked> <?php esc_html_e( 'Przykładowe produkty (25 sztuk z cenami, stanami i opisami)', 'printarium' ); ?></label></li>
						<li><label><input type="checkbox" name="printarium_steps[]" value="pages" checked> <?php esc_html_e( 'Podstrony (Oferta, Kontakt, O nas, FAQ, Dostawa, Regulamin, Polityka prywatności, Zwroty)', 'printarium' ); ?></label></li>
						<li><label><input type="checkbox" name="printarium_steps[]" value="menus" checked> <?php esc_html_e( 'Menu: główne, stopki i prawne (wraz z przypisaniem do lokalizacji)', 'printarium' ); ?></label></li>
						<li><label><input type="checkbox" name="printarium_steps[]" value="settings" checked> <?php esc_html_e( 'Ustawienia: strona główna, waluta PLN, format cen, ładne odnośniki', 'printarium' ); ?></label></li>
					</ul>

					<p>
						<button type="submit" class="button button-primary button-hero"><?php esc_html_e( 'Uruchom import', 'printarium' ); ?></button>
					</p>
					<p class="description"><?php esc_html_e( 'Produkty otrzymują wygenerowane zdjęcia zastępcze w kolorystyce motywu. Podmienisz je później na własne zdjęcia w edytorze produktu.', 'printarium' ); ?></p>
				</form>
			</div>

			<div class="printarium-card">
				<h2><?php esc_html_e( '2. Stan sklepu', 'printarium' ); ?></h2>
				<ul class="printarium-status">
					<li>
						<span><?php esc_html_e( 'WooCommerce', 'printarium' ); ?></span>
						<strong class="<?php echo $wc_active ? 'is-ok' : 'is-warn'; ?>"><?php echo $wc_active ? esc_html__( 'aktywne', 'printarium' ) : esc_html__( 'brak', 'printarium' ); ?></strong>
					</li>
					<li>
						<span><?php esc_html_e( 'Kategorie produktów', 'printarium' ); ?></span>
						<strong><?php echo esc_html( is_wp_error( $categories ) ? '0' : (string) $categories ); ?></strong>
					</li>
					<li>
						<span><?php esc_html_e( 'Opublikowane produkty', 'printarium' ); ?></span>
						<strong><?php echo esc_html( $products ? (string) $products->publish : '0' ); ?></strong>
					</li>
					<li>
						<span><?php esc_html_e( 'Menu główne', 'printarium' ); ?></span>
						<strong class="<?php echo has_nav_menu( 'primary' ) ? 'is-ok' : 'is-warn'; ?>"><?php echo has_nav_menu( 'primary' ) ? esc_html__( 'przypisane', 'printarium' ) : esc_html__( 'nieprzypisane', 'printarium' ); ?></strong>
					</li>
					<li>
						<span><?php esc_html_e( 'Strona główna', 'printarium' ); ?></span>
						<strong class="<?php echo 'page' === get_option( 'show_on_front' ) ? 'is-ok' : 'is-warn'; ?>"><?php echo 'page' === get_option( 'show_on_front' ) ? esc_html__( 'statyczna', 'printarium' ) : esc_html__( 'lista wpisów', 'printarium' ); ?></strong>
					</li>
				</ul>

				<h3><?php esc_html_e( 'Szybkie odnośniki', 'printarium' ); ?></h3>
				<p>
					<a class="button" href="<?php echo esc_url( admin_url( 'customize.php' ) ); ?>"><?php esc_html_e( 'Personalizator', 'printarium' ); ?></a>
					<a class="button" href="<?php echo esc_url( admin_url( 'nav-menus.php' ) ); ?>"><?php esc_html_e( 'Menu', 'printarium' ); ?></a>
					<a class="button" href="<?php echo esc_url( admin_url( 'widgets.php' ) ); ?>"><?php esc_html_e( 'Widgety / filtry', 'printarium' ); ?></a>
					<?php if ( $wc_active ) : ?>
						<a class="button" href="<?php echo esc_url( admin_url( 'edit.php?post_type=product' ) ); ?>"><?php esc_html_e( 'Produkty', 'printarium' ); ?></a>
					<?php endif; ?>
				</p>
			</div>

			<div class="printarium-card">
				<h2><?php esc_html_e( '3. Co dalej', 'printarium' ); ?></h2>
				<ol class="printarium-checklist">
					<li><?php esc_html_e( 'Wgraj logo i zdjęcie sekcji hero: Wygląd → Dostosuj → Printarium.', 'printarium' ); ?></li>
					<li><?php esc_html_e( 'Podmień zdjęcia zastępcze produktów i kategorii na własne fotografie.', 'printarium' ); ?></li>
					<li><?php esc_html_e( 'Uzupełnij treści podstron – wypełniono je tekstem przykładowym.', 'printarium' ); ?></li>
					<li><?php esc_html_e( 'Dodaj widgety filtrów do obszaru „Sidebar sklepu” (filtr ceny, kategorie, atrybuty).', 'printarium' ); ?></li>
					<li><?php esc_html_e( 'Skonfiguruj dostawę i płatności w ustawieniach WooCommerce.', 'printarium' ); ?></li>
					<li><?php esc_html_e( 'Zastąp regulamin i politykę prywatności dokumentami przygotowanymi prawnie.', 'printarium' ); ?></li>
				</ol>
			</div>

			<div class="printarium-card printarium-card--danger">
				<h2><?php esc_html_e( '4. Usuwanie danych demonstracyjnych', 'printarium' ); ?></h2>
				<p><?php esc_html_e( 'Usuwa wyłącznie elementy utworzone przez powyższy import (oznaczone wewnętrzną etykietą). Twoje własne produkty i strony pozostaną nietknięte.', 'printarium' ); ?></p>

				<form method="post" onsubmit="return confirm('<?php echo esc_js( __( 'Na pewno usunąć wszystkie dane demonstracyjne? Tej operacji nie można cofnąć.', 'printarium' ) ); ?>');">
					<?php wp_nonce_field( 'printarium_admin' ); ?>
					<input type="hidden" name="printarium_action" value="remove">
					<button type="submit" class="button button-secondary"><?php esc_html_e( 'Usuń dane demonstracyjne', 'printarium' ); ?></button>
				</form>
			</div>

		</div>
	</div>
	<?php
}

/**
 * Podpowiedź po aktywacji motywu.
 */
function printarium_admin_activation_notice() {
	global $pagenow;

	if ( 'themes.php' !== $pagenow || isset( $_GET['page'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		return;
	}

	if ( get_option( 'printarium_setup_done' ) ) {
		return;
	}
	?>
	<div class="notice notice-info is-dismissible">
		<p>
			<strong><?php esc_html_e( 'Motyw Printarium jest aktywny.', 'printarium' ); ?></strong>
			<?php esc_html_e( 'Uruchom kreator, aby utworzyć kategorie, przykładowe produkty, podstrony i menu.', 'printarium' ); ?>
			<a class="button button-primary" href="<?php echo esc_url( admin_url( 'themes.php?page=printarium' ) ); ?>"><?php esc_html_e( 'Przejdź do konfiguracji', 'printarium' ); ?></a>
		</p>
	</div>
	<?php
}
add_action( 'admin_notices', 'printarium_admin_activation_notice' );

/**
 * Oznacza konfigurację jako wykonaną po pierwszym imporcie.
 */
function printarium_mark_setup_done() {
	if ( isset( $_GET['page'], $_GET['done'] ) && 'printarium' === $_GET['page'] ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		update_option( 'printarium_setup_done', 1 );
	}
}
add_action( 'admin_init', 'printarium_mark_setup_done' );
