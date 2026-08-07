<?php
/**
 * Stopka.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

$printarium_email   = printarium_option( 'printarium_contact_email' );
$printarium_phone   = printarium_option( 'printarium_contact_phone' );
$printarium_address = printarium_option( 'printarium_contact_address' );
?>
	</div><!-- #content -->

	<footer id="colophon" class="site-footer">
		<div class="container">

			<div class="site-footer__top">

				<div class="site-footer__about">
					<?php printarium_site_branding(); ?>
					<p><?php echo wp_kses_post( printarium_option( 'printarium_footer_about' ) ); ?></p>
				</div>

				<div class="site-footer__col">
					<?php if ( is_active_sidebar( 'footer-1' ) ) : ?>
						<?php dynamic_sidebar( 'footer-1' ); ?>
					<?php else : ?>
						<h2 class="site-footer__heading"><?php esc_html_e( 'Sklep', 'printarium' ); ?></h2>
						<ul>
							<?php foreach ( printarium_get_shop_categories( 6 ) as $printarium_term ) : ?>
								<?php $printarium_link = get_term_link( $printarium_term ); ?>
								<?php if ( ! is_wp_error( $printarium_link ) ) : ?>
									<li><a href="<?php echo esc_url( $printarium_link ); ?>"><?php echo esc_html( $printarium_term->name ); ?></a></li>
								<?php endif; ?>
							<?php endforeach; ?>
						</ul>
					<?php endif; ?>
				</div>

				<div class="site-footer__col">
					<?php if ( is_active_sidebar( 'footer-2' ) ) : ?>
						<?php dynamic_sidebar( 'footer-2' ); ?>
					<?php else : ?>
						<h2 class="site-footer__heading"><?php esc_html_e( 'Informacje', 'printarium' ); ?></h2>
						<?php
						wp_nav_menu(
							array(
								'theme_location' => 'footer',
								'container'      => false,
								'menu_class'     => 'site-footer__menu',
								'depth'          => 1,
								'fallback_cb'    => '__return_empty_string',
							)
						);
						?>
					<?php endif; ?>
				</div>

				<div class="site-footer__col">
					<?php if ( is_active_sidebar( 'footer-3' ) ) : ?>
						<?php dynamic_sidebar( 'footer-3' ); ?>
					<?php else : ?>
						<h2 class="site-footer__heading"><?php esc_html_e( 'Kontakt', 'printarium' ); ?></h2>
						<ul class="footer-contact">
							<?php if ( $printarium_email ) : ?>
								<li><?php printarium_icon( 'mail', 18 ); ?><a href="mailto:<?php echo esc_attr( $printarium_email ); ?>"><?php echo esc_html( $printarium_email ); ?></a></li>
							<?php endif; ?>
							<?php if ( $printarium_phone ) : ?>
								<li><?php printarium_icon( 'phone', 18 ); ?><a href="tel:<?php echo esc_attr( preg_replace( '/[^0-9+]/', '', $printarium_phone ) ); ?>"><?php echo esc_html( $printarium_phone ); ?></a></li>
							<?php endif; ?>
							<?php if ( $printarium_address ) : ?>
								<li><?php printarium_icon( 'pin', 18 ); ?><span><?php echo esc_html( $printarium_address ); ?></span></li>
							<?php endif; ?>
						</ul>
					<?php endif; ?>
				</div>

			</div>

			<div class="site-footer__bottom">
				<p class="mb-0">
					<?php
					$printarium_copy = printarium_option( 'printarium_copyright' );

					if ( $printarium_copy ) {
						echo wp_kses_post( $printarium_copy );
					} else {
						printf(
							/* translators: 1: rok, 2: nazwa serwisu. */
							esc_html__( '© %1$s %2$s. Wszelkie prawa zastrzeżone.', 'printarium' ),
							esc_html( gmdate( 'Y' ) ),
							esc_html( get_bloginfo( 'name' ) )
						);
					}
					?>
				</p>

				<?php
				wp_nav_menu(
					array(
						'theme_location' => 'legal',
						'container'      => false,
						'menu_class'     => 'site-footer__legal',
						'depth'          => 1,
						'fallback_cb'    => '__return_empty_string',
					)
				);
				?>
			</div>

		</div>
	</footer>

</div><!-- #page -->

<?php wp_footer(); ?>
</body>
</html>
