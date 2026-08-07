<?php
/**
 * Brak produktów – stan pusty (sekcja 9 systemu projektowego 02).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;
?>
<div class="no-results">
	<span class="no-results__icon"><?php printarium_icon( 'box', 64 ); ?></span>
	<h2 class="no-results__title"><?php esc_html_e( 'Nie znaleziono produktów', 'printarium' ); ?></h2>
	<p class="no-results__text"><?php esc_html_e( 'Spróbuj zmienić lub usunąć filtry.', 'printarium' ); ?></p>
	<a class="btn btn--secondary" href="<?php echo esc_url( printarium_shop_base_url() ); ?>">
		<?php printarium_icon( 'refresh', 18 ); ?> <?php esc_html_e( 'Wyczyść filtry', 'printarium' ); ?>
	</a>
</div>
