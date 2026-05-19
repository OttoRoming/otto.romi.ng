<?php
ob_start();
?>


<h2>On this page</h2>
<ul>
    <li><a href="/kursmaterial">Kursmaterial</a></li>
</ul>

<?php
$content = ob_get_clean();
include "base.php";
?>