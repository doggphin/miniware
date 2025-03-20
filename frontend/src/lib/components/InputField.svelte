<script lang="ts">
    import TitledComponent from "./TitledComponent.svelte";

    interface Props {
        title : string,
        inputState : string
    };

    let { title, inputState: inputState = $bindable() } : Props = $props();
</script>


<TitledComponent title={title}>
    <input bind:value={inputState} placeholder={"Enter a value here..."}/>
</TitledComponent>
