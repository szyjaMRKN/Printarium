<?php
/**
 * Menu mobilne (sekcja 2 systemu projektowego 02).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;
?>
<div class="mobile-menu" id="mobile-menu" aria-hidden="true" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e( 'Menu główne', 'printarium' ); ?>">

	<div class="mobile-menu__head">
		<?php printarium_site_branding(); ?>
		<button type="button" class="header-action" data-printarium-menu-close aria-label="<?php esc_attr_e( 'Zamknij menu', 'printarium' ); ?>">
			<?php printarium_icon( 'close', 24 ); ?>
		</button>
	</div>

	<div class="mobile-menu__body">
		<?php
		wp_nav_menu(
			array(
				'theme_location' => 'primary',
				'container'      => false,
				'menu_class'     => 'mobile-menu__list',
				'fallback_cb'    => 'printarium_menu_fallback',
				'depth'          => 2,
			)
		);
		?>

		<div class="mt-3">
			<?php get_search_form(); ?>
		</div>
	</div>

	<div class="mobile-menu__foot">
		<?php if ( printarium_is_woocommerce_active() ) : ?>
			<a class="header-action" href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" aria-label="<?php esc_attr_e( 'Moje konto', 'printarium' ); ?>">
				<?php printarium_icon( 'user', 24 ); ?>
			</a>
			<a class="header-action" href="<?php echo esc_url( wc_get_cart_url() ); ?>" aria-label="<?php esc_attr_e( 'Koszyk', 'printarium' ); ?>">
				<?php printarium_icon( 'cart', 24 ); ?>
			</a>
		<?php endif; ?>
	</div>

</div>
