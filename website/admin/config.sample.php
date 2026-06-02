<?php
/**
 * 管理画面 設定サンプル
 *
 * 使い方:
 *   1) このファイルを config.php としてコピー
 *   2) ADMIN_USER とパスワードハッシュを設定
 *   3) config.php は Git にコミットしない（.gitignore 済み）
 *
 * パスワードハッシュの生成（サーバー上で1回だけ実行）:
 *   php -r "echo password_hash('ここに好きなパスワード', PASSWORD_DEFAULT), PHP_EOL;"
 * 出力された文字列を ADMIN_PASS_HASH に貼り付ける。
 */
declare(strict_types=1);

define('ADMIN_USER', 'admin');
define('ADMIN_PASS_HASH', '$2y$10$REPLACE_WITH_GENERATED_HASH'); // 上記コマンドで生成
