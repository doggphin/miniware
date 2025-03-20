<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        title : string,
        children : Snippet
    }

    let { title , children } : Props = $props();
</script>


<div class="title">
    {`${title}:`}
</div>
<div class="component">
    {@render children()}
</div>


<style>
    .title {
        font-size: var(--s16);
        margin-top: var(--s8);
    }
    .component {
        margin-top: var(--s4);
    }
</style>