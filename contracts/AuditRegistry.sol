// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IProofOfIntegrity {
    function isFinal(bytes32 root) external view returns (bool);
}

contract AuditRegistry {
    address public owner;
    address public poi;

    struct Bundle {
        string cid;
        address submitter;
        uint256 timestamp;
    }

    mapping(bytes32 => Bundle) public bundles;

    event BundleRegistered(bytes32 indexed root, string cid, address indexed submitter);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setProofOfIntegrity(address _poi) external onlyOwner {
        poi = _poi;
    }

    function registerBundle(bytes32 root, string calldata cid) external {
        require(IProofOfIntegrity(poi).isFinal(root), "not finalized");
        bundles[root] = Bundle(cid, msg.sender, block.timestamp);
        emit BundleRegistered(root, cid, msg.sender);
    }
}
