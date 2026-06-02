<?php
declare(strict_types=1);
session_start();
require __DIR__ . '/lib/db.php';

/* 送信先メール（運用時に変更） */
const ADMIN_MAIL = 'staff@rion-lab-japan.com';

/* CSRFトークン */
if (empty($_SESSION['csrf'])) {
    $_SESSION['csrf'] = bin2hex(random_bytes(32));
}

$errors  = [];
$old     = ['name' => '', 'company' => '', 'email' => '', 'phone' => '', 'category' => '', 'message' => '', 'agree' => ''];
$success = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($old as $k => $_) {
        $old[$k] = trim((string) ($_POST[$k] ?? ''));
    }

    // CSRF
    if (!hash_equals($_SESSION['csrf'], (string) ($_POST['csrf'] ?? ''))) {
        $errors['_'] = 'セッションの有効期限が切れました。お手数ですが再度送信してください。';
    }
    // ハニーポット（人間には見えない項目。値があればbot）
    if (!empty($_POST['website'])) {
        $errors['_'] = '送信に失敗しました。';
    }
    // 簡易レート制限（10秒に1回）
    if (!empty($_SESSION['last_submit']) && (time() - (int) $_SESSION['last_submit']) < 10) {
        $errors['_'] = '連続した送信は制限されています。少し時間をおいてお試しください。';
    }

    if ($old['name'] === '')                 $errors['name']    = 'お名前を入力してください。';
    if ($old['email'] === '')                $errors['email']   = 'メールアドレスを入力してください。';
    elseif (!filter_var($old['email'], FILTER_VALIDATE_EMAIL)) $errors['email'] = 'メールアドレスの形式が正しくありません。';
    if ($old['message'] === '')              $errors['message'] = 'お問い合わせ内容を入力してください。';
    elseif (mb_strlen($old['message']) > 5000) $errors['message'] = 'お問い合わせ内容が長すぎます。';
    if ($old['agree'] !== 'yes')             $errors['agree']   = '個人情報の取り扱いに同意してください。';

    if (!$errors) {
        try {
            $id = save_contact($old);
            $_SESSION['last_submit'] = time();

            // 管理者へ通知メール（失敗してもDB保存は完了済み）
            $subject = '【お問い合わせ】' . ($old['category'] ?: '一般') . ' / ' . $old['name'];
            $bodyTxt = "お問い合わせを受信しました（#{$id}）\n\n"
                . "お名前: {$old['name']}\n会社名: {$old['company']}\n"
                . "メール: {$old['email']}\n電話: {$old['phone']}\n種別: {$old['category']}\n\n"
                . "内容:\n{$old['message']}\n";
            $headers = 'From: no-reply@rion-lab-japan.com' . "\r\n"
                . 'Reply-To: ' . $old['email'] . "\r\n"
                . 'Content-Type: text/plain; charset=UTF-8';
            @mb_send_mail(ADMIN_MAIL, $subject, $bodyTxt, $headers);

            $success = true;
            $_SESSION['csrf'] = bin2hex(random_bytes(32)); // トークン再生成
            $old = array_fill_keys(array_keys($old), '');
        } catch (Throwable $e) {
            $errors['_'] = '送信中にエラーが発生しました。時間をおいて再度お試しください。';
        }
    }
}

function e(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
$categories = ['アプリ開発', 'Web制作・開発', 'バックエンド開発', 'QC・品質管理', '営業資料作成', 'SNS運用', '動画制作', 'DX研修', '採用・協業', 'その他'];
?>
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>お問い合わせ｜株式会社Rion Lab Japan</title>
  <meta name="description" content="株式会社Rion Lab Japanへのお問い合わせ。アプリ開発・Web制作・DX研修などのご相談はこちらから。">
  <meta name="robots" content="noindex">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Outfit:wght@500;600;700;800&family=Zen+Maru+Gothic:wght@500;700&family=Zen+Old+Mincho:wght@600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
  <link rel="stylesheet" href="assets/css/themes.css">
  <link rel="stylesheet" href="assets/css/base.css">
  <script src="assets/js/theme.js"></script>
</head>
<body>
  <header class="site-header">
    <nav class="nav container" aria-label="グローバルナビ">
      <a class="brand" href="index.html">
        <span class="brand__mark"><i class="fa-solid fa-flask"></i></span>
        <span class="brand__name">Rion Lab Japan<small>ITプロダクトのトータルサポート</small></span>
      </a>
      <button class="nav__toggle" aria-label="メニュー" aria-expanded="false"><i class="fa-solid fa-bars"></i></button>
      <ul class="nav__links">
        <li><a href="index.html">ホーム</a></li>
        <li><a href="services.html">サービス</a></li>
        <li><a href="company.html">会社情報</a></li>
        <li><a href="https://dx-lab.rion-lab-japan.com/" target="_blank" rel="noopener">DX研修ラボ</a></li>
        <li><a class="btn btn--primary nav__cta" href="contact.php" aria-current="page"><i class="fa-regular fa-envelope"></i> お問い合わせ</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <section class="page-hero">
      <div class="container">
        <p class="breadcrumb"><a href="index.html">ホーム</a> / お問い合わせ</p>
        <h1>Contact</h1>
        <p>ご相談・お見積り・採用・協業など、お気軽にお問い合わせください。担当者より折り返しご連絡いたします。</p>
      </div>
    </section>

    <section class="section" style="padding-top:0">
      <div class="container" style="max-width:760px">
        <?php if ($success): ?>
          <div class="alert alert--ok" role="status">
            <strong>送信が完了しました。</strong> お問い合わせいただきありがとうございます。担当者より折り返しご連絡いたします。
          </div>
        <?php else: ?>
          <?php if (!empty($errors['_'])): ?>
            <div class="alert alert--err" role="alert" style="margin-bottom:1.5rem"><?= e($errors['_']) ?></div>
          <?php endif; ?>

          <form class="form" method="post" action="contact.php" novalidate>
            <input type="hidden" name="csrf" value="<?= e($_SESSION['csrf']) ?>">
            <!-- ハニーポット（スパム対策・人間には非表示） -->
            <div class="honey" aria-hidden="true">
              <label>Webサイト<input type="text" name="website" tabindex="-1" autocomplete="off"></label>
            </div>

            <div class="field <?= isset($errors['name']) ? 'field--error' : '' ?>">
              <label for="name">お名前 <span class="req">必須</span></label>
              <input id="name" name="name" type="text" value="<?= e($old['name']) ?>" required>
              <?php if (isset($errors['name'])): ?><span class="field__err"><?= e($errors['name']) ?></span><?php endif; ?>
            </div>

            <div class="field">
              <label for="company">会社名・団体名</label>
              <input id="company" name="company" type="text" value="<?= e($old['company']) ?>">
            </div>

            <div class="field <?= isset($errors['email']) ? 'field--error' : '' ?>">
              <label for="email">メールアドレス <span class="req">必須</span></label>
              <input id="email" name="email" type="email" value="<?= e($old['email']) ?>" required>
              <?php if (isset($errors['email'])): ?><span class="field__err"><?= e($errors['email']) ?></span><?php endif; ?>
            </div>

            <div class="field">
              <label for="phone">電話番号</label>
              <input id="phone" name="phone" type="tel" value="<?= e($old['phone']) ?>">
            </div>

            <div class="field">
              <label for="category">お問い合わせ種別</label>
              <select id="category" name="category">
                <option value="">選択してください</option>
                <?php foreach ($categories as $c): ?>
                  <option value="<?= e($c) ?>" <?= $old['category'] === $c ? 'selected' : '' ?>><?= e($c) ?></option>
                <?php endforeach; ?>
              </select>
            </div>

            <div class="field <?= isset($errors['message']) ? 'field--error' : '' ?>">
              <label for="message">お問い合わせ内容 <span class="req">必須</span></label>
              <textarea id="message" name="message" required><?= e($old['message']) ?></textarea>
              <?php if (isset($errors['message'])): ?><span class="field__err"><?= e($errors['message']) ?></span><?php endif; ?>
            </div>

            <div class="field field--check <?= isset($errors['agree']) ? 'field--error' : '' ?>">
              <input id="agree" name="agree" type="checkbox" value="yes" <?= $old['agree'] === 'yes' ? 'checked' : '' ?> required>
              <label for="agree">個人情報を、お問い合わせ対応の目的に限り利用することに同意します。<span class="req">必須</span>
                <?php if (isset($errors['agree'])): ?><br><span class="field__err"><?= e($errors['agree']) ?></span><?php endif; ?>
              </label>
            </div>

            <div>
              <button class="btn btn--primary" type="submit"><i class="fa-solid fa-paper-plane"></i> 送信する</button>
              <p class="form-note" style="margin-top:.8rem">※ 通常2〜3営業日以内にご返信いたします。</p>
            </div>
          </form>
        <?php endif; ?>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer__bottom" style="border:0">
        <span>© 2026 株式会社Rion Lab Japan</span>
        <span>名古屋 / 川口 / ベトナム・ダナン</span>
      </div>
    </div>
  </footer>

  <div class="day-badge" data-day-badge aria-hidden="true"></div>
  <script src="assets/js/main.js" defer></script>
</body>
</html>
