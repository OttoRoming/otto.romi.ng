<?php
ob_start();

$dir = __DIR__;
$files = scandir($dir); ?>

<style>
    <?php include "fs.css"; ?>
</style>

<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>

<div class="files">
    <?php foreach ($files as $file) { ?>
        <a class="file" href="<?= htmlspecialchars($file) ?>">
            <div class="file-name"><?= htmlspecialchars($file) ?></div>
            <div class="file-content">
                <?php
                $ext = pathinfo($file, PATHINFO_EXTENSION);
                $img_exts = [
                    'png',
                    'jpg',
                    'jpeg',
                    'jpe',
                    'gif',
                    'webp',
                    'avif',
                    'svg',
                    'svgz',
                    'ico',
                    'cur',
                    'bmp',
                    'tif',
                    'tiff',
                    'jp2',
                    'j2k',
                    'heic',
                    'heif',
                    'jxl',
                    'apng',
                ];

                if (in_array($ext, $img_exts)) {
                    echo '<img src="' . htmlspecialchars($file) . '" alt="' . htmlspecialchars($file) . '" loading="lazy">';
                } else if (is_dir($file)) {
                    echo "<strong>Directory</strong><br>";
                    foreach (scandir($file) as $subfile) {
                        if ($subfile === "." || $subfile === "..") continue;
                        echo htmlspecialchars($subfile) . "/<br>";
                    }
                } else {
                    echo htmlspecialchars(file_get_contents($file));
                }
                ?>
            </div>
        </a>
    <?php } ?>
</div>

<br>
<br>
<br>

<?php
$content = ob_get_clean();
include "base.php";
?>