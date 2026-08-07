<?php
/**
 * Nagłówek strony.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;
?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">
	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<a class="skip-link" href="#primary"><?php esc_html_e( 'Przejdź do treści', 'printarium' ); ?></a>

<div id="page" class="site">

	<header id="masthead" class="site-header">
		<div class="container">
			<div class="site-header__inner">

				<?php printarium_site_branding(); ?>

				<nav class="primary-nav" aria-label="<?php esc_attr_e( 'Menu główne', 'printarium' ); ?>">
					<?php
					wp_nav_menu(
						array(
							'theme_location' => 'primary',
							'container'      => false,
							'menu_class'     => 'primary-nav__list',
							'fallback_cb'    => 'printarium_menu_fallback',
							'depth'          => 2,
						)
					);
					?>
				</nav>

				<div class="header-actions">
					<button type="button" class="header-action" data-printarium-search-toggle aria-expanded="false" aria-controls="header-search" aria-label="<?php esc_attr_e( 'Szukaj', 'printarium' ); ?>">
						<?php printarium_icon( 'search', 24 ); ?>
					</button>

					<?php if ( printarium_is_woocommerce_active() ) : ?>
						<a class="header-action" href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" aria-label="<?php esc_attr_e( 'Moje konto', 'printarium' ); ?>">
							<?php printarium_icon( 'user', 24 ); ?>
						</a>
						<?php echo printarium_get_cart_button(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<?php endif; ?>

					<button type="button" class="header-action nav-toggle" data-printarium-menu-open aria-label="<?php esc_attr_e( 'Otwórz menu', 'printarium' ); ?>" aria-controls="mobile-menu" aria-expanded="false">
						<?php printarium_icon( 'menu', 24 ); ?>
					</button>
				</div>

			</div>

			<div class="header-search" id="header-search">
				<?php get_search_form(); ?>
			</div>
		</div>
	</header>

	<?php get_template_part( 'template-parts/mobile-menu' ); ?>

	<?php if ( printarium_is_woocommerce_active() ) : ?>
		<div class="mini-cart-panel" id="mini-cart-panel" aria-hidden="true" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e( 'Twój koszyk', 'printarium' ); ?>">
			<div class="mini-cart-panel__head">
				<h2 class="mini-cart-panel__title"><?php esc_html_e( 'Twój koszyk', 'printarium' ); ?></h2>
				<button type="button" class="header-action" data-printarium-minicart-close aria-label="<?php esc_attr_e( 'Zamknij koszyk', 'printarium' ); ?>">
					<?php printarium_icon( 'close', 22 ); ?>
				</button>
			</div>
			<div class="mini-cart-panel__body widget woocommerce widget_shopping_cart">
				<div class="widget_shopping_cart_content"></div>
			</div>
		</div>
	<?php endif; ?>

	<div id="content" class="site-content">
