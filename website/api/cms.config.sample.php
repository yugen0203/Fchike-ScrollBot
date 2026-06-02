<?php
/**
 * microCMS 接続設定サンプル
 *
 * 使い方:
 *   1) このファイルを同じディレクトリに cms.config.php としてコピー
 *   2) microCMS 管理画面 → サービス設定 / API キー の値を記入
 *   3) cms.config.php は Git にコミットしない（.gitignore 済み）
 *
 * 例: サービスURLが https://rionlab.microcms.io なら SERVICE_DOMAIN は "rionlab"
 */
declare(strict_types=1);

define('MICROCMS_SERVICE_DOMAIN', 'your-service');     // サブドメイン部分
define('MICROCMS_API_KEY', 'xxxxxxxx-xxxx-xxxx-xxxx'); // 読み取り用APIキー
