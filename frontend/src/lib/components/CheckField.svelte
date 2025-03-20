<script lang="ts">
    import TitledComponent from "./TitledComponent.svelte";
    interface Props {
        title : string,
        enabledState : boolean
    }

    let { title, enabledState = $bindable() } : Props = $props();
</script>


<TitledComponent title={title}>
    <input type="checkbox" bind:checked={enabledState}>
</TitledComponent>


<style>
    input {
        transform: scale(1.5);
    }
</style>