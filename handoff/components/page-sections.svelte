<!--
  Three landing-page sections (Features, Engines, Pricing) lifted from the
  Svelte 5 prototype. Drop them into your existing route or split them into
  separate components as needed. The Engines section depends on
  ./EnginesPanel.svelte.
-->
<script>
  import EnginesPanel from './EnginesPanel.svelte';

  // Feature cards — content + icon name. Icon SVGs are inlined below.
  const featureCards = [
    {
      title: 'Fully Managed Infrastructure',
      body: "Don't worry about Kubernetes, CUDA versions, or configuring VPNs. Focus on deploying your model and serving customers.",
      icon: 'cloud'
    },
    {
      title: 'Autoscaling',
      body: 'Automatically scales up as traffic increases and down as it decreases to save on compute costs.',
      icon: 'scale'
    },
    {
      title: 'Observability',
      body: 'Understand and debug your model through comprehensive logs & metrics.',
      icon: 'metrics'
    },
    {
      title: 'Inference Engines',
      body: 'Deploy with vLLM, TGI, SGLang, TEI, or custom containers.',
      icon: 'engine'
    },
    {
      title: 'Hugging Face Integration',
      body: 'Download model weights fast and securely with seamless Hugging Face Hub integration.',
      icon: 'box'
    },
    {
      title: 'Future-proof AI Stack',
      body: 'Stay current with the latest frameworks and optimizations without managing complex upgrades.',
      icon: 'wrench'
    }
  ];

  const selfServePoints = [
    'Pay for what you use, per minute',
    'Starting as low as $0.06/hour',
    'Billed monthly',
    'Email support'
  ];
  const enterprisePoints = [
    'Lower marginal costs based on volume',
    'Uptime guarantees',
    'Custom annual contracts',
    'Dedicated support, SLAs'
  ];
</script>

<!-- ============================================================
     FEATURES SECTION
     ============================================================ -->
<section class="border-b border-gray-200/70 px-4">
  <div
    class="mx-auto grid max-w-7xl divide-gray-200/70 border-x border-gray-200/70 max-lg:divide-y lg:grid-cols-5 lg:divide-x"
  >
    <div class="flex flex-col justify-center p-8 sm:p-10 lg:col-span-2 lg:p-14">
      <span
        class="text-smd mb-4 inline-block max-w-fit rounded-full bg-amber-400/10 px-4 py-1 font-semibold text-amber-600"
        >Features</span
      >
      <h2 class="mb-6 text-3xl font-bold text-balance text-gray-900 md:text-4xl">
        Everything you need to deploy AI models at scale
      </h2>
      <p class="mb-2 text-lg text-gray-600">
        Fully managed infrastructure, autoscaling, and built-in observability — so you can focus on
        your model, not the ops.
      </p>
    </div>
    <div
      class="grid gap-px divide-dashed divide-gray-200 bg-white max-md:divide-y md:grid-cols-3 md:divide-x lg:col-span-3"
    >
      {#each featureCards as card}
        <article class="flex flex-col p-6 sm:p-8">
          <div class="mb-3 flex size-9 items-center justify-center rounded-md bg-gray-50">
            {#if card.icon === 'cloud'}
              <svg class="size-5 text-sky-500" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.5 19h-11a4.5 4.5 0 0 1-1-8.9A6 6 0 0 1 18 9a4 4 0 0 1-.5 10z" />
              </svg>
            {:else if card.icon === 'scale'}
              <svg class="size-5 text-emerald-500" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 8V4h4M20 8V4h-4M4 16v4h4M20 16v4h-4" />
                <path d="M7 7l10 10M17 7L7 17" />
              </svg>
            {:else if card.icon === 'metrics'}
              <svg class="size-5 text-rose-500" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="13" width="4" height="7" rx="1" />
                <rect x="10" y="8" width="4" height="12" rx="1" />
                <rect x="17" y="3" width="4" height="17" rx="1" />
              </svg>
            {:else if card.icon === 'engine'}
              <svg class="size-5 text-violet-500" viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" />
              </svg>
            {:else if card.icon === 'box'}
              <svg class="size-5 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7l9 5 9-5-9-5-9 5zM3 7v10l9 5 9-5V7M12 12v10" />
              </svg>
            {:else if card.icon === 'wrench'}
              <svg class="size-5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path
                  d="M14.7 6.3a4 4 0 0 1 5 5L18 13l4 4-3 3-4-4-1.7 1.7a4 4 0 0 1-5-5L7 14 4 11l3-3 3 3 1.3-1.3a4 4 0 0 1 3.4-1.4z"
                />
              </svg>
            {/if}
          </div>
          <h3 class="mb-1 text-base font-semibold text-gray-900">{card.title}</h3>
          <p class="text-sm text-gray-500">{card.body}</p>
        </article>
      {/each}
    </div>
  </div>
</section>

<!-- ============================================================
     ENGINES SECTION — uses EnginesPanel.svelte for the right column
     ============================================================ -->
<section class="border-b border-gray-200/70 px-4">
  <div
    class="mx-auto grid max-w-7xl divide-gray-200/70 border-x border-b border-gray-200/70 max-lg:divide-y lg:grid-cols-5 lg:divide-x"
  >
    <div class="flex flex-col justify-center p-8 sm:p-10 lg:col-span-2 lg:p-14">
      <span
        class="text-smd mb-4 inline-block max-w-fit rounded-full bg-emerald-400/10 px-4 py-1 font-semibold text-emerald-600"
        >Engines</span
      >
      <h2 class="mb-6 text-3xl font-bold text-balance text-gray-900 md:text-4xl">
        Powered by the best open-source inference engines
      </h2>
      <p class="mb-8 text-lg text-gray-600">
        Deploy with TGI, vLLM, SGLang, llama.cpp or bring your own custom container — all with zero
        infrastructure overhead.
      </p>
    </div>
    <div class="relative z-1 grid lg:col-span-3 overflow-hidden">
      <EnginesPanel />
    </div>
  </div>
</section>

<!-- ============================================================
     PRICING SECTION
     ============================================================ -->
<section class="border-b border-gray-200/70 px-4">
  <div
    class="mx-auto grid max-w-7xl divide-gray-200/70 border-x border-gray-200/70 max-lg:divide-y lg:grid-cols-5 lg:divide-x"
  >
    <div class="flex flex-col justify-center p-8 sm:p-10 lg:col-span-2 lg:p-14">
      <span
        class="text-smd mb-4 inline-block max-w-fit rounded-full bg-rose-400/10 px-4 py-1 font-semibold text-rose-600"
        >Pricing</span
      >
      <h2 class="mb-6 text-3xl font-bold text-balance text-gray-900 md:text-4xl">
        Choose a plan that fits your needs
      </h2>
      <p class="mb-8 text-lg text-gray-600">
        Start with pay-as-you-go pricing, or scale up with a tailored enterprise contract — only pay
        for the compute you actually use.
      </p>
    </div>
    <div
      class="relative z-1 grid gap-px divide-dashed divide-gray-200 bg-white max-md:divide-y md:grid-cols-2 md:divide-x lg:col-span-3"
    >
      <article class="flex flex-col bg-white/40 py-4">
        <header class="border-b border-dashed border-gray-200 p-4 sm:px-8 sm:py-6">
          <div class="mb-1 flex items-center gap-2">
            <svg class="size-5 text-gray-800" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true">
              <path d="M25.798 10a10 10 0 0 0-19.62.124A7.496 7.496 0 0 0 7.5 25H8v-2h-.5a5.496 5.496 0 0 1-.377-10.98l.837-.057.09-.833A7.993 7.993 0 0 1 23.737 10Z" />
            </svg>
            <h3 class="text-xl font-bold text-gray-900">Self-Serve</h3>
          </div>
          <p class="text-sm text-gray-500">Pay as you go when using Inference Endpoints</p>
        </header>
        <main class="border-b border-dashed border-gray-200 p-4 sm:px-8 sm:py-6">
          <a
            href="https://huggingface.co/pricing#endpoints"
            class="flex items-center justify-center gap-1.5 rounded-xl border-2 border-white bg-black px-5 py-2.5 text-base font-semibold text-white"
            >See Instance Pricing</a
          >
        </main>
        <footer class="space-y-3 p-4 pb-6 sm:px-8 sm:py-6 sm:pb-10">
          {#each selfServePoints as item}
            <li class="flex items-start gap-2.5 text-sm">
              <span class="flex size-5 items-center justify-center rounded-full bg-blue-50 text-blue-500">+</span>
              <span class="text-gray-600">{item}</span>
            </li>
          {/each}
        </footer>
      </article>
      <article class="flex flex-col bg-white/40 py-4">
        <header class="border-b border-dashed border-gray-200 p-4 sm:px-8 sm:py-6">
          <div class="mb-1 flex items-center gap-2">
            <svg class="size-5 text-gray-800" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true">
              <path d="M28 12H18a2.002 2.002 0 0 0-2 2v4h-4a2.002 2.002 0 0 0-2 2v10h20V14a2.002 2.002 0 0 0-2-2M12 28v-8h4v8Zm16 0H18V14h10Z" />
              <path d="M20 16h2v4h-2zm4 0h2v4h-2zm-4 6h2v4h-2zm4 0h2v4h-2z" />
            </svg>
            <h3 class="text-xl font-bold text-gray-900">Enterprise</h3>
          </div>
          <p class="text-sm text-gray-500">Get a custom quote and premium support</p>
        </header>
        <main class="border-b border-dashed border-gray-200 p-4 sm:px-8 sm:py-6">
          <a
            href="https://huggingface.co/contact/sales?from=enterprise"
            class="flex items-center justify-center gap-1.5 rounded-xl border-2 border-white bg-black px-5 py-2.5 text-base font-semibold text-white"
            >Request a Quote</a
          >
        </main>
        <footer class="space-y-3 p-4 pb-6 sm:px-8 sm:py-6 sm:pb-10">
          {#each enterprisePoints as item}
            <li class="flex items-start gap-2.5 text-sm">
              <span class="flex size-5 items-center justify-center rounded-full bg-blue-50 text-blue-500">+</span>
              <span class="text-gray-600">{item}</span>
            </li>
          {/each}
        </footer>
      </article>
    </div>
  </div>
</section>
