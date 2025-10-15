// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ProofChain {
    mapping(bytes32 => bool) public finalized;

    event Finalized(bytes32 indexed root, address indexed caller);

    function finalize(bytes32 root) external {
        finalized[root] = true;
        emit Finalized(root, msg.sender);
    }

    function isFinal(bytes32 root) external view returns (bool) {
        return finalized[root];
    }
}
