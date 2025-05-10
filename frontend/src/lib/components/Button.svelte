<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        onClick : Function,
        children : Snippet
    };

    let { onClick, children } : Props = $props();
</script>


<button class="styled-button clickable" onclick={() => onClick()}>
    {@render children?.()}
</button>