<?php
/**
 * cms.php — microCMS プロキシ
 *
 * フロント(assets/js/cms.js)からの GET を受け、microCMS の API へ中継する。
 * APIキーはサーバー側の cms.config.php にのみ保持し、ブラウザへ晒さない。
 * 設定が無い場合は 503 を返し、フロントは内蔵フォールバックで表示する。
 *
 * 設定方法: cms.config.sample.php を cms.config.php にコピーして値を記入。
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=UTF-8');

$conf = __DIR__ . '/cms.config.php';
if (!is_file($conf)) {
    http_response_code(503);
    echo json_encode(['error' => 'cms_not_configured']);
    exit;
}
require $conf; // MICROCMS_SERVICE_DOMAIN, MICROCMS_API_KEY を定義

if (!defined('MICROCMS_SERVICE_DOMAIN') || !defined('MICROCMS_API_KEY') || MICROCMS_API_KEY === '') {
    http_response_code(503);
    echo json_encode(['error' => 'cms_not_configured']);
    exit;
}

/* 許可するエンドポイントのみ（任意のAPI叩きを防ぐ） */
$allowed = ['news'];
$endpoint = preg_replace('/[^a-z0-9_\-]/i', '', (string) ($_GET['endpoint'] ?? 'news'));
if (!in_array($endpoint, $allowed, true)) {
    http_response_code(400);
    echo json_encode(['error' => 'invalid_endpoint']);
    exit;
}
$limit = max(1, min(20, (int) ($_GET['limit'] ?? 5)));

/* 簡易ファイルキャッシュ（5分） */
$cacheFile = sys_get_temp_dir() . '/microcms_' . $endpoint . '_' . $limit . '.json';
if (is_file($cacheFile) && (time() - filemtime($cacheFile) < 300)) {
    echo file_get_contents($cacheFile);
    exit;
}

$url = sprintf(
    'https://%s.microcms.io/api/v1/%s?limit=%d&orders=-publishedAt',
    MICROCMS_SERVICE_DOMAIN, $endpoint, $limit
);

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER     => ['X-MICROCMS-API-KEY: ' . MICROCMS_API_KEY],
    CURLOPT_TIMEOUT        => 8,
]);
$body = curl_exec($ch);
$code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($body === false || $code < 200 || $code >= 300) {
    // 失敗時は古いキャッシュがあれば返す、無ければ 502
    if (is_file($cacheFile)) {
        echo file_get_contents($cacheFile);
        exit;
    }
    http_response_code(502);
    echo json_encode(['error' => 'upstream_failed', 'status' => $code]);
    exit;
}

@file_put_contents($cacheFile, $body);
echo $body;
