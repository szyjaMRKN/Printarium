<?php
/**
 * Strona 404.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="site-main">
	<div class="container container--narrow error-404">

		<p class="error-404__code">404</p>
		<h1><?php esc_html_e( 'Nie znaleziono strony', 'printarium' ); ?></h1>
		<p class="text-muted mb-3"><?php esc_html_e( 'Ta strona nie istnieje lub została przeniesiona. Sprawdź adres albo skorzystaj z wyszukiwarki.', 'printarium' ); ?></p>

		<?php get_search_form(); ?>

		<p class="mt-5">
			<a class="btn btn--primary" href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'Wróć na stronę główną', 'printarium' ); ?></a>
			<?php if ( printarium_is_woocommerce_active() ) : ?>
				<a class="btn btn--secondary" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>"><?php esc_html_e( 'Przejdź do sklepu', 'printarium' ); ?></a>
			<?php endif; ?>
		</p>

	</div>
</main>

<?php
get_footer();
