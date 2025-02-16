<script lang="ts">
    interface Props {
        text: string,
        onClick : Function
    };

    let { text, onClick } : Props = $props();
</script>



<button onclick={() => {onClick()}}>
    {text}
</button>