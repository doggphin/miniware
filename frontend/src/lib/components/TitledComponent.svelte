<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        title : string,
        children : Snippet
    }

    let { title , children } : Props = $props();
</script>


<div>
    {`${title}:`}
</div>
<div>
    {@render children()}
</div>