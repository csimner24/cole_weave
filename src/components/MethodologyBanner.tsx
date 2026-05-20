export default function MethodologyBanner() {
  return (
    <section className="border-l-4 border-gray-300 bg-gray-50 px-6 py-5 rounded-r-lg">
      <p className="text-sm leading-relaxed text-gray-700">
        We score engineers across three dimensions.{" "}
        <span className="font-semibold text-blue-600">Volume</span> is total
        output: commits plus lines added and deleted in merged PRs.{" "}
        <span className="font-semibold text-green-600">Issues Closed</span> is
        how many issues they actually resolve, not just open.{" "}
        <span className="font-semibold text-purple-600">Breadth</span> is how
        many parts of the codebase they touch. Someone who ranks high in all
        three is consistently shipping, closing the loop, and working across
        the whole system.
      </p>
    </section>
  );
}
