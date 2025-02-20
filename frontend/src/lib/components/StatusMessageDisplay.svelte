<script lang="ts">
    import { StatusMessage } from "$lib/scripts/statusMessage";

    let { statusMessage }: { statusMessage : StatusMessage } = $props();
</script>



<div>
    {#if statusMessage.message}
        <div class="vertical-spacer"></div>
        <span style="color: {statusMessage.status == "error" ? "red" : statusMessage.status == "success" ? "green" : "var(--clr-primary)"};">{statusMessage.message}</span>
    {/if}
</div>



<style>
    div {
        margin-top: var(--s16);
    }
</style>