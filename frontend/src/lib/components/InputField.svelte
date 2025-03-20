<script lang="ts">
    import TitledComponent from "./TitledComponent.svelte";

    interface Props {
        title : string,
        inputState : string
    };

    let { title, inputState: inputState = $bindable() } : Props = $props();
</script>


<TitledComponent title={title}>
    <input class="bordered" bind:value={inputState} placeholder={"Enter a value here..."}/>
</TitledComponent>


<style>
    input {
        border-radius: var(--s4);
        padding: var(--s8);
        width: 100%;
    }
</style>
