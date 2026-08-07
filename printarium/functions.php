<?php
/**
 * Printarium – plik startowy motywu.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

define( 'PRINTARIUM_VERSION', '1.0.0' );
define( 'PRINTARIUM_DIR', trailingslashit( get_template_directory() ) );
define( 'PRINTARIUM_URI', trailingslashit( get_template_directory_uri() ) );

require_once PRINTARIUM_DIR . 'inc/setup.php';
require_once PRINTARIUM_DIR . 'inc/icons.php';
require_once PRINTARIUM_DIR . 'inc/enqueue.php';
require_once PRINTARIUM_DIR . 'inc/template-tags.php';
require_once PRINTARIUM_DIR . 'inc/customizer.php';
require_once PRINTARIUM_DIR . 'inc/shortcodes.php';
require_once PRINTARIUM_DIR . 'inc/woocommerce.php';
require_once PRINTARIUM_DIR . 'inc/demo-content.php';
require_once PRINTARIUM_DIR . 'inc/admin-page.php';
