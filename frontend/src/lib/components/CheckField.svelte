<script lang="ts">
    interface Props {
        enabledState : boolean
    }

    let { enabledState = $bindable() } : Props = $props();
</script>



<input type="checkbox" bind:checked={enabledState}>